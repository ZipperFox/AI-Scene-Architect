"""Blender integration fixture only: no edit or revision of the v0.2 scenes."""
import json
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/ai-scene-architect/scripts'))
import bpy
from scene_plan import PlanError, digest, load_plan, read_json
from reference_scout import bind_research, compile_bundle
from build_scene import main as build_main

out=Path(sys.argv[sys.argv.index('--')+1])
if out.exists():raise ValueError('Use a new test result path')
checks={}
for name in ('crystal-mine','woodwork-shop'):
    plan=load_plan(ROOT/'examples/reference-scout'/name/'scene_plan.json')
    checks[name+'_loads_in_blender']=bool(plan['research']['decision_bindings'])

with tempfile.TemporaryDirectory(prefix='scout-integration-') as directory:
    temp=Path(directory)
    source=ROOT/'examples/reference-scout/woodwork-shop'
    manifest=read_json(source/'reference_manifest.json')
    bundle=compile_bundle(manifest,temp/'bundle')
    plan=load_plan(source/'scene_plan.json')
    # Deliberately small technical fixture; not presented as a finished workshop.
    plan.pop('research')
    plan['id']='scout-integration-fixture'
    plan['purpose']='Technical reference-bundle serialization fixture only.'
    plan['objects']=[o for o in plan['objects'] if o['id'] in ('floor','storage_lower')]
    plan['paths']=[]
    bound=bind_research(plan,bundle)
    plan_path=bundle/'scene_plan.json'
    plan_path.write_text(json.dumps(bound,ensure_ascii=False,indent=2),encoding='utf-8')
    sentinel=bpy.data.objects.new('protected_sentinel',None)
    bpy.context.scene.collection.objects.link(sentinel)
    brief=bundle/'art_direction_brief.md'
    original=brief.read_bytes();brief.write_bytes(original+b'\nTAMPERED')
    sys.argv=['build_scene.py','--','--plan',str(plan_path),'--output',str(temp/'must-not-build')]
    try:
        build_main()
        checks['tamper_rejected_before_scene_mutation']=False
    except PlanError:
        checks['tamper_rejected_before_scene_mutation']='protected_sentinel' in bpy.data.objects and not (temp/'must-not-build').exists()
    brief.write_bytes(original)
    target=temp/'new-fixture'
    sys.argv=['build_scene.py','--','--plan',str(plan_path),'--output',str(target)]
    build_main()
    checks['fixture_blend_and_glb_created']=(target/'scene.blend').is_file() and (target/'scene.glb').is_file()
    checks['portable_bundle_copied']=all((target/name).is_file() and digest(target/name)==digest(bundle/name)
        for name in ('reference_manifest.json','art_direction_brief.md'))
    checks['copied_plan_validates_after_relocation']=bool(load_plan(target/'scene_plan.json')['research'])

result={'blender':bpy.app.version_string,'checks':checks,'all_passed':all(checks.values()),
        'scope':'Temporary floor/crate fixture; no v0.2 scene or revision journal changed.'}
out.parent.mkdir(parents=True,exist_ok=True)
with out.open('x',encoding='utf-8') as handle:json.dump(result,handle,indent=2)
print(json.dumps(result))
if not result['all_passed']:raise RuntimeError('Reference Scout Blender integration failed')
