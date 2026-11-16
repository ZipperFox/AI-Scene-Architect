"""Assemble a validated AI-authored scene plan in a NEW editable .blend + GLB.

blender --background --factory-startup --python-exit-code 1 --python build_scene.py
  -- --plan scene_plan.json --output new-directory [--revision 1 --history reviews.json]
"""
import argparse
import json
import math
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
from mathutils import Vector
from builders import build_asset, create_material
from iteration_guard import decide
from scene_plan import PlanError, digest, read_json, load_plan


def bounds(objects):
    points=[o.matrix_world @ Vector(v) for o in objects for v in o.bound_box]
    return [[min(p[i] for p in points) for i in range(3)],
            [max(p[i] for p in points) for i in range(3)]]


def scene_metrics():
    depsgraph=bpy.context.evaluated_depsgraph_get()
    meshes={}
    for obj in bpy.context.scene.objects:
        if obj.type!='MESH':
            continue
        evaluated=obj.evaluated_get(depsgraph)
        mesh=evaluated.to_mesh()
        mesh.calc_loop_triangles()
        bad=sum(not all(math.isfinite(c) for c in v.co) for v in mesh.vertices)
        degenerate=sum(t.area<1e-10 for t in mesh.loop_triangles)
        meshes[obj.name]={'vertices':len(mesh.vertices),'triangles':len(mesh.loop_triangles),
                          'invalid_vertices':bad,'degenerate_triangles':degenerate,
                          'bounds':bounds([obj]),'materials':[m.name for m in obj.data.materials if m],
                          'parent':obj.parent.name if obj.parent else None}
        evaluated.to_mesh_clear()
    return {'meshes':meshes,'mesh_count':len(meshes),
            'triangles':sum(m['triangles'] for m in meshes.values()),
            'invalid_vertices':sum(m['invalid_vertices'] for m in meshes.values()),
            'degenerate_triangles':sum(m['degenerate_triangles'] for m in meshes.values()),
            'bounds':bounds([o for o in bpy.context.scene.objects if o.type=='MESH'])}


def intersection(a,b,tolerance=.015):
    return all(min(a[1][i],b[1][i])-max(a[0][i],b[0][i])>tolerance for i in range(3))


def layout_checks(plan, groups):
    boxes={name:bounds(parts) for name,parts in groups.items()}
    errors=[];warnings=[];contacts=[]
    items={o['id']:o for o in plan['objects']}
    for name,obj in items.items():
        if 'support' not in obj:
            continue
        support=boxes[obj['support']];box=boxes[name]
        gap=box[0][2]-support[1][2]
        xy=all(min(box[1][i],support[1][i])-max(box[0][i],support[0][i])>.001 for i in range(2))
        ok=abs(gap)<=.025 and xy
        contacts.append({'object':name,'support':obj['support'],'vertical_gap':gap,'xy_overlap':xy,'pass':ok})
        if not ok:
            errors.append(f'{name}: unsupported placement, gap {gap:.4f}')
    names=list(groups)
    # Inter-object evaluated part bounds, not whole-frame bounds: openings stay open.
    # Bounds overlaps are candidates, not proof of surface penetration.
    part_boxes={n:[bounds([o]) for o in groups[n]] for n in names}
    for i,a in enumerate(names):
        for b in names[i+1:]:
            if items[a].get('support')==b or items[b].get('support')==a:
                continue
            if b in items[a].get('allow_overlap_with',[]) or a in items[b].get('allow_overlap_with',[]):
                continue
            if intersection(boxes[a],boxes[b]) and any(intersection(x,y) for x in part_boxes[a] for y in part_boxes[b]):
                warnings.append({'kind':'overlap_candidate','objects':[a,b]})
    for path in plan['paths']:
        blocked=set()
        r=path['width']/2
        for a,b in zip(path['points'],path['points'][1:]):
            steps=max(2,int((Vector(b)-Vector(a)).length/.15))
            for step in range(steps+1):
                point=Vector(a).lerp(Vector(b),step/steps)
                for name,parts in part_boxes.items():
                    for box in parts:
                        if box[1][2]<=point.z+.15 or box[0][2]>=point.z+1.9:
                            continue
                        dx=max(box[0][0]-point.x,0,point.x-box[1][0])
                        dy=max(box[0][1]-point.y,0,point.y-box[1][1])
                        if dx*dx+dy*dy<r*r:
                            blocked.add(name)
        if blocked:
            warnings.append({'kind':'path_clearance_candidate','path':path['id'],'objects':sorted(blocked)})
    return {'errors':errors,'warnings':warnings,'contacts':contacts,
            'method':'Evaluated part AABBs and sampled path discs; visual review remains required.'}


def authorize_revision(revision, history):
    if revision<0 or revision>2:
        raise PlanError('Revision must be 0, 1 or 2; initial render is 0')
    if revision==0:
        if history and Path(history).exists():
            raise PlanError('Existing history cannot be reset for an initial build')
        return
    if not history:
        raise PlanError('A revision requires cumulative visual-review history')
    reviews=read_json(history)
    decision=decide(reviews)
    if decision['decision']!='continue' or reviews[-1]['iteration']!=revision-1:
        raise PlanError('Revision not authorized by guard: '+json.dumps(decision))


def assemble(plan):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene
    scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48
    scene.cycles.use_denoising=True
    scene.render.resolution_x=768;scene.render.resolution_y=768;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.world=bpy.data.worlds.new(plan['id']+'_world')
    background=scene.world.node_tree.nodes.get('Background')
    background.inputs['Color'].default_value=(*plan['world_color'],1)
    background.inputs['Strength'].default_value=.35
    scene.view_settings.view_transform='AgX'
    materials={m['id']:create_material(m) for m in plan['materials']}
    assets={a['id']:{**a,'parameters':dict(a['parameters'])} for a in plan['assets']}
    for asset in assets.values():
        asset['parameters'].setdefault('seed',plan['seed'])
    cache={};groups={}
    for spec in plan['objects']:
        root=bpy.data.objects.new(spec['id'],None)
        scene.collection.objects.link(root)
        root['asa_asset']=spec['asset'];root['asa_purpose']=spec['purpose']
        root['asa_plan_position']=spec['position']
        asset=assets[spec['asset']]
        if spec['asset'] not in cache:
            parts=build_asset(asset,[materials[m] for m in asset['materials']])
            cache[spec['asset']]=[(o.data,o.name.split('__',1)[-1]) for o in parts]
        else:
            parts=[]
            for mesh,label in cache[spec['asset']]:
                part=bpy.data.objects.new(label,mesh)
                scene.collection.objects.link(part);parts.append(part)
        for part,(_,label) in zip(parts,cache[spec['asset']]):
            part.name=spec['id']+'__'+label
            part.parent=root
            part['asa_object']=spec['id']
        root.rotation_euler=[math.radians(v) for v in spec['rotation']]
        root.scale=spec['scale']
        root.location=spec['position']
        bpy.context.view_layer.update()
        # Base-Z means lowest transformed vertex, even after tilt and scaling.
        root.location.z+=spec['position'][2]-bounds(parts)[0][2]
        bpy.context.view_layer.update()
        groups[spec['id']]=parts
    for spec in plan['lights']:
        data=bpy.data.lights.new(spec['id'],spec['type']);data.energy=spec['energy'];data.color=spec['color']
        if spec['type']=='AREA':data.shape='DISK';data.size=spec['size']
        elif spec['type']=='POINT':data.shadow_soft_size=spec['size']
        obj=bpy.data.objects.new(spec['id'],data);scene.collection.objects.link(obj)
        obj.location=spec['position']
        obj.rotation_euler=(Vector(spec['target'])-obj.location).to_track_quat('-Z','Y').to_euler()
    for spec in plan['cameras']:
        data=bpy.data.cameras.new(spec['id']);data.lens=spec['lens'];data.clip_end=2000
        if spec['ortho_scale']>0:data.type='ORTHO';data.ortho_scale=spec['ortho_scale']
        obj=bpy.data.objects.new(spec['id'],data);scene.collection.objects.link(obj)
        obj.location=spec['position']
        obj.rotation_euler=(Vector(spec['target'])-obj.location).to_track_quat('-Z','Y').to_euler()
    scene.camera=bpy.data.objects[plan['hero_camera']]
    scene['asa_scene_id']=plan['id']
    return groups


def main():
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--revision',type=int,default=0);p.add_argument('--history',type=Path)
    args=p.parse_args(argv)
    plan=load_plan(args.plan)
    authorize_revision(args.revision,args.history)
    target=args.output.resolve()
    if target.exists():
        raise PlanError('Output directory must be NEW; refusing any overwrite: '+str(target))
    # Refuse in-memory source scenes too, before deleting startup objects.
    if bpy.data.filepath:
        raise PlanError('Use --factory-startup with no input .blend; existing sources are never edited')
    target.mkdir(parents=True)
    shutil.copyfile(args.plan,target/'scene_plan.json')
    if 'research' in plan:
        from reference_scout import validate_plan_research
        for reference in validate_plan_research(plan,args.plan.resolve().parent):
            shutil.copyfile(reference,target/reference.name)
    source_dir=target/'source';source_dir.mkdir()
    source_hashes={}
    for source in Path(__file__).resolve().parent.glob('*.py'):
        shutil.copyfile(source,source_dir/source.name)
        source_hashes[source.name]=digest(source)
    groups=assemble(plan)
    layout=layout_checks(plan,groups)
    (target/'layout-checks.json').write_text(json.dumps(layout,indent=2),encoding='utf-8')
    if layout['errors']:
        raise PlanError('Unsupported objects: '+str(layout['errors']))
    metrics=scene_metrics()
    if metrics['invalid_vertices'] or metrics['degenerate_triangles']:
        raise PlanError('Invalid or degenerate geometry; see builder')
    blend=target/'scene.blend';glb=target/'scene.glb'
    bpy.context.scene['asa_plan_sha256']=digest(args.plan)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',export_apply=True,
                              export_cameras=True,export_lights=True,export_extras=True,
                              export_animations=False)
    manifest={'scene':plan['id'],'blender_version':bpy.app.version_string,
              'blender_executable':bpy.app.binary_path,'revision':args.revision,
              'plan_sha256':digest(args.plan),'source_blend':str(blend),'glb':str(glb),
              'generator_sha256':source_hashes,
              'blend_sha256':digest(blend),'glb_sha256':digest(glb),'metrics':metrics,
              'layout':layout,'cameras':[c['id'] for c in plan['cameras']],
              'material_export':'PBR factors/emission portable; procedural bump stays Blender-only. Area/world lights are not supported in GLB; relight in target engine.'}
    (target/'build-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('ASA_BUILD_MANIFEST='+str(target/'build-manifest.json'))


if __name__=='__main__':
    main()
