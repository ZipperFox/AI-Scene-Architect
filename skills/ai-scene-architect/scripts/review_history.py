"""Append a real image review without truncating/resetting an existing journal.

An exclusive lock serializes cooperating writers. The reviewer remains responsible
for actually opening the images; this utility verifies their hashes, not vision.
"""
import argparse
import json
import os
from pathlib import Path

from iteration_guard import decide, validate
from scene_plan import PlanError, digest, read_json


def append_review(history_path, review, manifest_path):
    path=Path(history_path)
    path.parent.mkdir(parents=True,exist_ok=True)
    lock=path.with_name(path.name+'.lock')
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    try:
        os.close(fd)
        history=read_json(path) if path.exists() else []
        if history and decide(history)['decision']!='continue':
            raise PlanError('The existing journal has stopped; cannot append or reset it')
        if review.get('iteration')!=len(history):
            raise PlanError('Review iteration must append consecutively; never reset history')
        manifest=read_json(manifest_path)
        expected={name:info['sha256'] for name,info in manifest['viewpoints'].items()}
        if set(expected)!={'hero','three_quarter','top'}:
            raise PlanError('Manifest must contain the three preview viewpoints')
        if review.get('renders')!=expected:
            raise PlanError('Review must include all three actual manifest hashes')
        for info in manifest['viewpoints'].values():
            image=Path(info['path'])
            if not image.is_absolute():
                image=Path(manifest_path).resolve().parent/image
            if digest(image)!=info['sha256']:
                raise PlanError('Image has changed since rendering')
        history.append(review)
        validate(history)
        temporary=path.with_name(path.name+'.pending')
        with temporary.open('x',encoding='utf-8') as handle:
            json.dump(history,handle,ensure_ascii=False,indent=2)
            handle.flush();os.fsync(handle.fileno())
        os.replace(temporary,path)
        return decide(history)
    finally:
        lock.unlink()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--history',required=True,type=Path)
    p.add_argument('--review',required=True,type=Path)
    p.add_argument('--manifest',required=True,type=Path)
    args=p.parse_args()
    print(json.dumps(append_review(args.history,read_json(args.review),args.manifest),indent=2))


if __name__=='__main__':
    main()
