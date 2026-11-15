# Scene planning request

建立小型開放剖面的低模木工作坊：工作桌、長凳、木箱、木製柱樑與手動繩索絞盤。保留中央走道，暖木色配灰白牆，日光從開放前側照入，沒有水晶或礦洞。

Read `D:\AI_work\AI-Scene-Architect\skills\ai-scene-architect\references\scene-planning.md` and the schema
`D:\AI_work\AI-Scene-Architect\skills\ai-scene-architect\references\scene-plan.schema.json`. Act as the planner: infer a
purposeful layout, real-scale dimensions, circulation, asset inventory, material
palette, lights and at least three informative cameras from this brief. Produce
scene_plan.json, not executable code. Use the builder catalog, but do not copy an
example layout or select a fixed scene template. Record assumptions and layout
rationale in art_direction, zones and paths. Validate with scripts/scene_plan.py.
If the brief needs unsupported forms, state the gap; do not silently substitute
unrelated objects. All transforms use meters, Z-up, degrees, object base Z.
After building, actually inspect images and use the existing iteration guard;
the initial render is iteration 0, at most two revisions, no total time limit.
