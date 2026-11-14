---
name: ai-scene-architect
description: Plan and improve 3D scenes in Blender with procedural modeling, multi-view rendering, image-based art direction, bounded visual revisions, and export preparation. Use when building Blender models or scenes, critiquing generated 3D art, reducing generic AI-looking results, or preparing game environments.
---

# AI Scene Architect

## Workflow

1. Capture the user's intent: audience, game or render purpose, camera, style, palette, visual references, scale, silhouette, asset constraints, platform, and explicit non-negotiables. Do not choose an unrelated generic aesthetic. Separate confirmed requirements from proposals.
2. Make a scene/asset plan. Reuse suitable assets first. Build missing procedural geometry in Blender using Python. Preserve approved source files and object identifiers; work on a versioned copy for meaningful edits.
3. Verify scene geometry and render at least three informative angles using `scripts/render_previews.py`. Provide the input `.blend` explicitly and record the preview manifest. Use `--engine cycles-cpu` if headless Eevee is unsupported. Impose an external process timeout. Don't assume the Blender API version equals the AI agent's Python version.
4. **Open and visually inspect the PNGs.** Follow `references/visual-quality.md`. If no image-reading tool is available, stop the autonomous visual review, retain the images, and ask for a human review. Never claim a quality pass based on a successful render command alone.
5. Record each review using the same issue identifiers, severity, visual evidence, and suggested minimal fix. Maintain a chronological JSON review history. Run `scripts/iteration_guard.py` before changing anything. If it says `stop`, report the actual reason and do not work around the guard.
6. For each approved revision, change only the targeted scene elements; re-render, inspect, compare with the previous version, and append a review. Hard limit: two revisions by default. No redesign of user-approved silhouettes, identity, layouts, or style without permission.
7. Deliver the scene version, preview images, issue list, resolved/unresolved items, guard decision, and any engine-specific validation performed. State what has not been verified.

## Required visual quality gates

- Composition: clear focal point, readable silhouette, intentional negative space, useful camera angle.
- Modeling: coherent proportions, joining/overlap quality, non-repetitive shapes, no floating or clipping objects.
- Materials: meaningful surface roughness and variation, controlled colors, no uniform plastic appearance unless requested.
- Lighting: separation of subject and background, readable exposure, consistent light direction and shadow design.
- Purpose: game readability and performance for game assets; reference fidelity for reconstruction; approved art style always wins.

Visual scores are subjective evidence, not laboratory measurements. Use issues and before/after images; do not fabricate a quantitative aesthetic score or treat random detail/noise as progress.

## Hard stopping rules

- Revision budget reached (default 2 after initial render), regardless of perceived quality.
- New render hashes identical to the previous iteration.
- No reduction in tracked issue severity for two consecutive revisions.
- The same ineffective change signature appears twice in a row while the issue set is unchanged.
- User-approved aesthetic or geometry constraints would have to be violated.
- Image inspection is unavailable or a required action lacks authorization.

Stop and show remaining issues. Do **not** reset the history to evade the limit. A new task or explicit user direction can start another controlled run.

## Tools

- `scripts/render_previews.py`: blender background mode; scene preview + SHA-256 manifest; never overwrites the source scene.
- `scripts/iteration_guard.py`: standard Python; deterministic stop/continue decision based on the JSON review history.
- `references/visual-quality.md`: visual critique prompts and review format.
