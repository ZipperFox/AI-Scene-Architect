"""Post-build artifact and refusal checks; no scene edits or visual corrections."""
import argparse
import json
import struct
import subprocess
import sys
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/ai-scene-architect/scripts'))
from iteration_guard import decide
from scene_plan import digest, read_json


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--blender',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args()
    out=ROOT/'evidence/v02'
    if args.output.exists():raise ValueError('Audit result must be a new file')
    checks={};commands=[]
    scripts=ROOT/'skills/ai-scene-architect/scripts'
    mine=ROOT/'output/v02/crystal-mine/iteration-2'
    plan=ROOT/'examples/crystal-mine/scene_plan.json'
    def reject(label,script,options,input_blend=None):
        command=[str(args.blender),'--background','--factory-startup','--disable-autoexec']
        if input_blend:command.append(str(input_blend))
        command+=['--python-exit-code','1','--python',str(scripts/script),'--',*map(str,options)]
        run=subprocess.run(command,capture_output=True,encoding='utf-8',errors='replace')
        with (out/(args.output.stem+'-'+label+'.log')).open('x',encoding='utf-8') as handle:
            handle.write(run.stdout+run.stderr)
        commands.append({'label':label,'command':command,'exit_code':run.returncode})
        checks[label]=run.returncode==1
    reject('reject-existing-output','build_scene.py',['--plan',plan,'--output',mine])
    not_created=out/'must-not-create-loaded-source'
    reject('reject-loaded-source','build_scene.py',['--plan',plan,'--output',not_created],mine/'scene.blend')
    checks['loaded_source_output_absent']=not not_created.exists()
    not_created=out/'must-not-create-revision-three'
    reject('reject-third-revision','build_scene.py',['--plan',plan,'--output',not_created,'--revision',3,'--history',mine.parent/'visual-history.json'])
    checks['third_revision_output_absent']=not not_created.exists()
    not_created=out/'must-not-create-invalid-camera'
    reject('reject-invalid-camera','render_previews.py',['--output',not_created,'--camera-names','missing','missing2','missing3'],mine/'scene.blend')
    checks['invalid_camera_output_absent']=not not_created.exists()
    old=read_json(out/'pr1-preservation-before.json')
    checks['all_pr1_evidence_unchanged']=all(Path(item['Path']).is_file() and digest(item['Path'])==item['Hash'].lower() for item in old)
    checks['all_versioned_sources_unchanged']=True
    checks['all_png_hashes_and_headers_valid']=True
    for manifest_path in (ROOT/'output/v02').glob('*/iteration-*/build-manifest.json'):
        m=read_json(manifest_path);base=manifest_path.parent
        checks['all_versioned_sources_unchanged'] &= digest(base/'scene.blend')==m['blend_sha256'] and digest(base/'scene.glb')==m['glb_sha256']
    for manifest_path in (ROOT/'output/v02').glob('*/iteration-*/*previews/manifest.json'):
        m=read_json(manifest_path)
        for view in m['viewpoints'].values():
            image=Path(view['path']);data=image.read_bytes()
            checks['all_png_hashes_and_headers_valid'] &= digest(image)==view['sha256'] and data[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',data[16:24])==(768,768)
    mine_history=read_json(mine.parent/'visual-history.json')
    checks['mine_exactly_two_revisions_no_reset']=[r['iteration'] for r in mine_history]==[0,1,2] and decide(mine_history)['reason']=='revision_budget_reached'
    shop_history=read_json(ROOT/'output/v02/woodwork-shop/visual-history.json')
    checks['shop_stops_after_one_revision']=decide(shop_history)['reason']=='no_remaining_issues' and len(shop_history)==2
    # Compare the default v0.1 camera path's newly rendered PNGs with the
    # preserved validation artifacts; this is a regression, not a scene revision.
    baseline=read_json(ROOT/'evidence/pr1-windows/測試場景 空白路徑/previews iteration-0/manifest.json')
    regression=read_json(out/'v01-regression/manifest.json')
    def pixel_payload(path):
        # PNG text/time metadata legitimately changes between renders. Compare
        # IHDR plus decompressed IDAT scanlines, not the file's metadata bytes.
        data=Path(path).read_bytes();offset=8;compressed=b'';header=None
        while offset<len(data):
            size=struct.unpack('>I',data[offset:offset+4])[0]
            kind=data[offset+4:offset+8];chunk=data[offset+8:offset+8+size]
            if kind==b'IHDR':header=chunk
            if kind==b'IDAT':compressed+=chunk
            offset+=size+12
        return header,zlib.decompress(compressed)
    checks['v01_default_pixel_payload_identical']=all(pixel_payload(baseline['viewpoints'][name]['path'])==pixel_payload(regression['viewpoints'][name]['path']) for name in baseline['viewpoints'])
    result={'checks':checks,'all_passed':all(checks.values()),'refusal_commands':commands}
    with args.output.open('x',encoding='utf-8') as handle:json.dump(result,handle,indent=2)
    print(json.dumps(result,indent=2))
    if not result['all_passed']:raise RuntimeError('Artifact audit failed')


if __name__=='__main__':main()
