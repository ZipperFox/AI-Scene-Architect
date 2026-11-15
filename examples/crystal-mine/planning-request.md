# Scene planning request

建立小型、低模風格的奇幻水晶礦洞，包含不規則洞穴岩壁、木製支架、不同大小的發光水晶、一輛廢棄礦車、散落礦石、入口與主要探索區域，燈光與構圖合理。

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
