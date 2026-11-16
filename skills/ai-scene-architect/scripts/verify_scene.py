"""Fresh-process reopen/import checks against a build manifest; never saves input.

Run with no input .blend, -- --manifest build-manifest.json --mode blend|glb
--output new-verification.json. GLB validation compares world bounds, mesh names,
triangle counts, material coverage and hierarchy against authored evaluated data.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy
from build_scene import scene_metrics
from scene_plan import digest, preview_cameras, read_json


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',required=True,type=Path)
    p.add_argument('--mode',required=True,choices=('blend','glb'))
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--render-output',type=Path,help='Optional fresh-import geometry previews with diagnostic relighting')
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise ValueError('Verification output already exists')
    manifest=read_json(args.manifest)
    source=args.manifest.resolve().parent/('scene.blend' if args.mode=='blend' else 'scene.glb')
    before=digest(source)
    if args.mode=='blend':
        bpy.ops.wm.open_mainfile(filepath=str(source))
    else:
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
        bpy.ops.import_scene.gltf(filepath=str(source))
    actual=scene_metrics();expected=manifest['metrics']
    plan=read_json(args.manifest.resolve().parent/'scene_plan.json')
    material_checks={}
    for spec in plan['materials']:
        material=bpy.data.materials.get(spec['id'])
        shader=material.node_tree.nodes.get('Principled BSDF') if material and material.node_tree else None
        if shader:
            actual_color=list(shader.inputs['Base Color'].default_value)[:3]
            glow=shader.inputs['Emission Color'].default_value
            strength=shader.inputs['Emission Strength'].default_value
            if spec.get('texture_style','none')!='none':
                textures=[n.image for n in material.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
                color_ok=False
                if textures:
                    image=textures[0];values=list(image.pixels)
                    means=[sum(values[i::4])/(len(values)/4) for i in range(3)]
                    expected_mean=manifest.get('texture_means',{}).get(spec['id'],spec['color'])
                    color_ok=list(image.size)==[128,128] and all(abs(means[i]-expected_mean[i])<.025 for i in range(3))
            else:color_ok=all(abs(actual_color[i]-spec['color'][i])<.002 for i in range(3))
            material_checks[spec['id']]=color_ok and abs(shader.inputs['Roughness'].default_value-spec['roughness'])<.002 and abs(shader.inputs['Metallic'].default_value-spec['metallic'])<.002 and all(abs(glow[i]*strength-spec['color'][i]*spec['emission'])<.002 for i in range(3))
        else:material_checks[spec['id']]=False
    names_match=set(actual['meshes'])==set(expected['meshes'])
    deviations=[]
    for name,a in actual['meshes'].items():
        if name not in expected['meshes']:
            continue
        e=expected['meshes'][name]
        if max(abs(a['bounds'][i][j]-e['bounds'][i][j]) for i in range(2) for j in range(3))>.002:
            deviations.append(name+': world bounds')
        if a['triangles']!=e['triangles']:
            deviations.append(name+': triangles')
        if not a['materials'] or set(a['materials'])!=set(e['materials']):
            deviations.append(name+': material assignment')
        if a['parent']!=e['parent']:
            deviations.append(name+': parent')
    checks={'source_hash_matches_build':before==manifest['blend_sha256' if args.mode=='blend' else 'glb_sha256'],
            'source_unchanged':before==digest(source),'mesh_names_match':names_match,
            'triangle_count_matches':actual['triangles']==expected['triangles'],
            'no_invalid_vertices':actual['invalid_vertices']==0,
            'no_degenerate_triangles':actual['degenerate_triangles']==0,
            'portable_pbr_material_factors_match':all(material_checks.values()),
            'per_mesh_geometry_material_hierarchy_matches':not deviations,
            'all_meshes_have_uvs':all(bool(o.data.uv_layers) for o in bpy.context.scene.objects if o.type=='MESH')}
    result={'mode':args.mode,'blender_version':bpy.app.version_string,'checks':checks,
            'deviations':deviations,'material_checks':material_checks,'all_passed':all(checks.values()),'metrics':actual}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as handle:json.dump(result,handle,indent=2)
    print('ASA_VERIFY='+json.dumps(checks))
    if not result['all_passed']:raise RuntimeError('Fresh-process verification failed')
    if args.render_output:
        from render_previews import main as render_main
        from mathutils import Vector
        # glTF omits area/world lighting. Rebuild diagnostic lighting explicitly;
        # these views validate exported geometry, not authored-light equivalence.
        for light in [o for o in bpy.context.scene.objects if o.type=='LIGHT']:
            bpy.data.objects.remove(light,do_unlink=True)
        for name,position,energy in [('export_key',(3,-6,10),1600),('export_fill',(-5,1,7),1100)]:
            data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.size=6
            obj=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(obj)
            obj.location=position
            obj.rotation_euler=(Vector((0,0,1))-obj.location).to_track_quat('-Z','Y').to_euler()
        bpy.context.scene.world=bpy.data.worlds.new('export_diagnostic_world')
        bpy.context.scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.15,.17,.2,1)
        sys.argv=['render_previews.py','--','--output',str(args.render_output),'--resolution','768',
                  '--samples','32','--engine','cycles-cpu','--camera-names',*preview_cameras(plan)]
        render_main()


if __name__=='__main__':main()
