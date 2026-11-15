"""Prepare a text-to-plan request for an image-capable AI agent, without a fixed scene template."""
import argparse
from pathlib import Path


def planning_request(brief):
    if not brief.strip():
        raise ValueError('The brief must not be empty')
    root = Path(__file__).resolve().parents[1]
    return f'''# Scene planning request

{brief.strip()}

Read `{root / 'references/scene-planning.md'}` and the schema
`{root / 'references/scene-plan.schema.json'}`. Act as the planner: infer a
purposeful layout, real-scale dimensions, circulation, asset inventory, material
palette, lights and at least three informative cameras from this brief. Produce
scene_plan.json, not executable code. Use the builder catalog, but do not copy an
example layout or select a fixed scene template. Record assumptions and layout
rationale in art_direction, zones and paths. Validate with scripts/scene_plan.py.
If the brief needs unsupported forms, state the gap; do not silently substitute
unrelated objects. All transforms use meters, Z-up, degrees, object base Z.
After building, actually inspect images and use the existing iteration guard;
the initial render is iteration 0, at most two revisions, no total time limit.
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--brief', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    request = planning_request(args.brief.read_text(encoding='utf-8-sig'))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as handle:
        handle.write(request)


if __name__ == '__main__':
    main()
