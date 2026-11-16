"""Technical artifact evidence only; no aesthetic metric or scene mutations."""
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'skills/ai-scene-architect/scripts'))
from iteration_guard import decide
from scene_plan import digest,load_plan

before=json.loads((OUT/'preservation-before.json').read_text())
checks={'all_prior_files_unchanged':all((ROOT/p).is_file() and digest(ROOT/p)==h for p,h in before.items())}
for scene in ('crystal-mine','woodwork-shop'):
    root=ROOT/'output/v03'/scene
    history=json.loads((root/'visual-history.json').read_text(encoding='utf-8'))
    checks[scene+'_consecutive_two_revisions']=[r['iteration'] for r in history]==[0,1,2]
    checks[scene+'_stopped']=decide(history)['decision']=='stop'
    checks[scene+'_bound_plan_valid']=bool(load_plan(ROOT/'examples/v03'/scene/'scene_plan.json')['research'])
    for path in root.glob('iteration-*/build-manifest.json'):
        manifest=json.loads(path.read_text());directory=path.parent
        checks[str(directory.relative_to(ROOT))+'_source_hashes']=digest(directory/'scene.blend')==manifest['blend_sha256'] and digest(directory/'scene.glb')==manifest['glb_sha256']
    final=root/'iteration-2'
    for mode in ('blend','glb'):
        checks[scene+'_'+mode+'_fresh_import']=json.loads((final/('verify-'+mode+'.json')).read_text())['all_passed']
    for folder in ('previews','glb-previews'):
        manifest=json.loads((final/folder/'manifest.json').read_text())
        checks[scene+'_'+folder+'_hashes']=len(manifest['viewpoints'])==3 and all(digest(v['path'])==v['sha256'] for v in manifest['viewpoints'].values())

for source in (ROOT/'output/v03').glob('*/iteration-*/source'):
    archive=source.parent/'source-snapshot.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as handle:
        for path in source.glob('*.py'):handle.write(path,path.name)
result={'checks':checks,'all_passed':all(checks.values()),'preserved_files':len(before),
        'scope':'File integrity, journals, plan provenance and executed technical checks only; no beauty score.'}
with (OUT/'artifact-audit.json').open('x',encoding='utf-8') as handle:json.dump(result,handle,indent=2)
print(json.dumps(result,indent=2))
if not result['all_passed']:raise RuntimeError('v0.3 artifact audit failed')
