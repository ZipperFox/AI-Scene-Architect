# Validate a researched scene direction with actual renders

Research is an input, not proof of beauty. Translate the Art Direction Brief
into actual changes to shape, proportions, layout, materials and lighting. Keep
the scene's required functional parts and the user's style. Add builder support
only where a visible deficiency requires it; more code or object count is not
the success criterion.

1. Freeze the baseline: source revision, .blend/GLB hashes, exact old renders,
   cameras/settings, existing defects and requirements. Never rewrite the old
   journal or the only source. A new visual task needs explicit user authorization
   before starting its own initial render and independent journal.
2. Inspect the baseline and relevant reference images. Record what you actually
   saw, source/media URLs and use/rights limits. Separate reference observation,
   AI interpretation and chosen implementation. Do not ship copyrighted images
   as scene textures or pretend unseen images were reviewed.
3. Build a complete initial candidate into a new directory. Reopen .blend,
   reimport GLB and render three informative views. Technical build failures
   before an initial render are recorded as failed attempts, not as successful
   visual iterations. Keep failed output; retry in a new directory.
4. Open all actual authored images. Review composition/focal hierarchy,
   proportions, rock/timber structure, material distinctions, light/mood,
   occlusion/contacts and conspicuous procedural repetition. Record image-based
   issues in the existing review format and append via `review_history.py`.
5. Consult the unchanged guard before correction. Use the same journal with
   `--revision 1` or `2` and a fresh output path. No overall time limit and no new
   automatic stopping threshold is introduced. Repetition and lack of progress
   still only warn. At the budget limit, stop and list unresolved defects.
6. Compare the retained version to actual old PNGs. Preserve matching hero and
   overview cameras, engine, resolution, samples and color management where
   practical. Explicitly label changed diagnostic angles; never crop, relight or
   recolor an old render to manufacture a win. A comparison board may only label
   and arrange images. Pixel changes prove difference, not improvement.
7. Report technical results, visible quality judgments and remaining unknowns
   separately. Use per-case `PASS_WITH_WARNINGS`, `FAIL` or `UNCLEAR` for the
   AI's visual assessment, with exact views/reasons. A failed scene stays failed
   even if every Python test passes. Keep all journals, native files and exports.

For same-camera comparisons, geometry/material/light changes are the intended
variables. Before/after evidence from one creator on two scenes is not a blinded
or causal benchmark of Reference Scout, models or agent skill. A demonstrated
improvement supports that case, not a guarantee across future scenes. User art
acceptance remains distinct from the AI's self-review.

v0.3 extensions keep legacy builder defaults: `cave_shell` is a connected,
front/top cutaway chamber; `window_wall` provides a real aperture and timber
frame; `platform` provides a clipped plinth; `furniture/table + craft_detail`
provides long boards, open dog holes, vise and purposeful work objects, while
`furniture/tool_rack` adds restrained wall storage. Optional `texture_style`
packs original 128×128 sRGB albedo, never reference photos. Procedural bump and
AREA/world lights remain Blender-specific; relit GLB diagnostics validate export
appearance under a different setup, not original-light equivalence.
