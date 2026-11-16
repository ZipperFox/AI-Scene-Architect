# Text to editable scene plans (v0.2)

The AI agent is the planner. The Python CLI does not impersonate an LLM and
does not map keywords to a fixed mine, room or workshop template. Start with the
user's actual brief. `prepare_planning.py` creates a request for a compatible
agent; the agent writes `scene_plan.json` against [the schema](scene-plan.schema.json).
No hosted model credentials or paid 3D-generation service are required by the
assembler. A standalone Python process cannot understand a new text brief.

Before a new plan, run [AI Reference Scout](reference-scout.md). The AI develops
its own aesthetic direction using real-world, fantasy or science-fiction
inspiration; references do not dictate beauty or require realism. Pass the
compiled bundle to `prepare_planning.py --references`, then bind the authored
plan to its manifest/brief. The optional `research` field stores byte hashes and
decision-to-plan value bindings; `load_plan` validates them before Blender runs.
Legacy v0.2 plans remain compatible. Researching future ideas does not reset an
existing scene's exhausted visual correction budget.

## Planning decisions

1. Preserve specified style and purpose. Record inferred scale, presentation
   boundaries and other assumptions in `art_direction`, rather than silently
   replacing the brief. Use three mood words and one concrete focal relationship.
2. Set meters, Z-up, XY origin and room/scene extent. Define occupied zones and
   routes wide enough for the intended use. A path is a declared inspection
   corridor, not an exported navigation mesh or proof of gameplay accessibility.
3. Inventory reusable `assets` separately from positioned `objects`. Each asset
   selects a builder, dimensions, materials and parameters; instances specify
   position, rotation and scale. Reuse the same asset for structurally identical
   pieces, vary seeds only when a natural form actually needs a new mesh.
4. Plan supports before clutter. Objects use **world XY and base Z**, not center
   Z. `support` references an existing object's top; it checks contact and does
   not silently reposition objects. A floor at Z=-0.2, height 0.2 has top Z=0.
   A crate on a table needs base Z equal to the table's actual top. Origins of
   imported/exported assembly roots remain editable, with semantic part names.
5. Select lights and at least three cameras for the purpose: hero, complementary
   construction view and overview. `hero_camera` explicitly selects the first
   rendered view; the other two come from the remaining camera list in order.
6. Validate, build into a new directory, open the images, and record concrete
   issues. Do not select one of the example plans in response to an unrelated
   brief. Unsupported forms require a scoped builder extension or an explicit
   limitation, not an unrelated primitive substitute.

## Builder catalog

All dimensions are overall local XYZ dimensions before instance scale and
rotation. All builders fit their editable parts within those dimensions, center
in XY and put the base at Z=0. The assembler transforms the group, then aligns
its transformed bounding-box base to planned Z. Rotated irregular geometry and
non-flat supports still require visual/contact review.

| kind | Form / parameters | Material order |
|---|---|---|
| ground, wall, beam | solid structural panel/member; `bevel` in meters | primary |
| rock | seeded faceted ico-derived mass; `seed`, `roughness` 0–0.4 | stone |
| rock_wall | continuous shared-vertex triangulated relief slab, irregular rim; `seed`, `roughness`, `segments` 4–32 | stone |
| timber_frame | paired posts, lintel, knee braces, iron shoes and bolts; `braces`, `bevel` | timber, iron |
| crystal | irregular polygon rings and pointed tip; `seed`, `segments` 4–32 | crystal |
| furniture | `variant`: table / bench / crate; planks, legs/aprons/stretchers or hollow boarded box; `bevel` | timber, metal straps |
| mechanism | `variant`: minecart / winch; hollow hopper, chassis, four wheels/axles/rivets, or supported drum/shaft/crank/cable turns; `bevel` | body, metal, rope |

Natural forms keep broad intentional facets; manufactured wood uses modest
edge relief; metal and rope have distinct response and construction detail.
Do not assign the same bevel, smooth shading or noise density to every object.
The catalog is reusable but finite: it is not an arbitrary topology generator.

Materials store portable base color, roughness, metallic and restrained emission.
`surface` and `variation` add Blender-native procedural bump; wood has directional
grain scaling. Geometry has simple per-face projected UVs. These UVs overlap and
are not packed lightmap or baking layouts. Procedural bump is not baked into GLB.
GLB preserves PBR factors and geometry; area and world lighting need relighting
in the target renderer. See [Blender's glTF manual](https://docs.blender.org/manual/en/5.3/addons/scene_gltf2.html).

## Validation boundaries

The bundled Draft 2020-12 schema is portable. `scene_plan.py` validates the
keywords used by this schema without dependencies, and fails on unsupported
keywords; it is not a general JSON Schema library. Semantic checks additionally
reject broken material/asset/camera/support links, duplicate names, invalid
builder variants and support cycles. Unknown fields fail rather than disappearing.

The Blender build refuses existing output directories and any loaded `.blend`.
It checks support top gaps/XY overlap, evaluated topology, inter-object part
AABB overlap candidates and sampled route clearance. Contacts use bounds, not a
general collision solver. Intended structural intersections must be declared in
`allow_overlap_with`, with a construction explanation in `purpose`; do not use
exemptions to conceal unrelated collisions. A clear AABB report cannot certify
surface contact, structural load bearing or absence of every mesh intersection.

`run_scene.py` invokes fresh Blender processes for build, three-view rendering,
blend reopen and GLB import, recording commands, exit status, source hashes,
per-mesh metrics and export diagnostic previews. Its result is **technical only**;
the agent must open both authored and exported images before accepting them.

## Review journal

Use the v0.1 review format in [visual-quality.md](visual-quality.md). Preserve one
history per requested scene, shared across versioned output directories. Append
via `review_history.py` with the corresponding preview manifest. It verifies
all three image hashes and refuses nonconsecutive appends, history resets,
appends after `stop`, or a concurrent journal writer. `visual_reviewed` remains
a declaration by a reviewer; hashes do not prove that an image was understood.

Before revision N, run the existing guard on the cumulative history. Pass
`--revision N --history <same journal>` to the builder/pipeline. Revision 0 is the
initial build, revisions 1 and 2 are the entire default correction budget. The
builder refuses revision 3, an existing journal for revision 0, or an absent,
stopped or mismatched journal for a correction. No total time limit is imposed.
Repeated edits, identical outputs and lack of progress are warnings only.
When stopped, report remaining issues; never delete/recreate the journal or
rename the scene to work around the limit. These are cooperating agent tools,
not a security boundary against someone intentionally deleting files.

If a journal write is interrupted, inspect `.lock`/`.pending` before manual
recovery; do not discard an existing history. The previous history is replaced
atomically only after the appended review has been validated and flushed.
