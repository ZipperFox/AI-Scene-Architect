"""Build, render, reopen and reimport in separate Blender processes.

Produces technical evidence only; the AI must OPEN images and append a visual
review before any revision. No packages, hosted model or paid 3D service needed.
"""
import argparse
import json
import subprocess
from pathlib import Path

from scene_plan import digest, preview_cameras, load_plan


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--blender',required=True,type=Path)
    p.add_argument('--plan',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--revision',type=int,default=0)
    p.add_argument('--history',type=Path)
    args=p.parse_args()
    blender=args.blender.resolve();plan_path=args.plan.resolve();out=args.output.resolve()
    plan=load_plan(plan_path)
    if not blender.is_file():p.error('Blender executable does not exist')
    if out.exists():p.error('Output must be a new directory')
    scripts=Path(__file__).resolve().parent
    commands=[]
    def run(label,script,arguments,input_blend=None):
        command=[str(blender),'--background','--factory-startup','--disable-autoexec']
        if input_blend:command.append(str(input_blend))
        command+=['--python-exit-code','1','--python',str(scripts/script),'--',*map(str,arguments)]
        result=subprocess.run(command,capture_output=True,encoding='utf-8',errors='replace')
        # No timeout: the agreed loop has no overall wall-clock limit.
        out.mkdir(parents=True,exist_ok=True)
        (out/(label+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
        commands.append({'stage':label,'command':command,'exit_code':result.returncode})
        if result.returncode:
            raise RuntimeError(f'{label} failed (exit {result.returncode}); see {out/(label+".log")}')
        print(label+': PASS',flush=True)
    arguments=['--plan',plan_path,'--output',out,'--revision',args.revision]
    if args.history:arguments+=['--history',args.history.resolve()]
    try:
        run('build','build_scene.py',arguments)
        before=digest(out/'scene.blend')
        run('render','render_previews.py',['--output',out/'previews','--resolution',768,
            '--samples',48,'--engine','scene','--camera-names',*preview_cameras(plan)],out/'scene.blend')
        if digest(out/'scene.blend')!=before:raise RuntimeError('Rendering changed the source blend')
        for mode in ('blend','glb'):
            extra=['--render-output',out/'glb-previews'] if mode=='glb' else []
            run('verify-'+mode,'verify_scene.py',['--manifest',out/'build-manifest.json','--mode',mode,
                '--output',out/('verify-'+mode+'.json'),*extra])
        passed=True
    finally:
        if out.exists():
            (out/'pipeline-report.json').write_text(json.dumps({'commands':commands,
                'technical_pass':locals().get('passed',False),'visual_review':'REQUIRED: open all images; do not infer quality from exit codes.'},indent=2),encoding='utf-8')
    print('Technical checks passed; visual review is still required.')


if __name__=='__main__':main()
