# AI Scene Architect

An open-source [Agent Skill](https://agentskills.io/) for AI-directed Blender scene creation, visual review, and controlled iteration.

**Current status: visual feedback foundation (v0.1).** This repository does **not** yet generate complete scenes autonomously. The implemented foundation renders a scene from several viewpoints and makes the AI's visual revision loop bounded and auditable.

## What makes it different

The skill requires an agent to *look at actual renders*, identify concrete visual problems, make targeted changes, and compare the next render to the previous one. Rendering a PNG is not the same as evaluating its quality. The AI agent must have image-viewing capability; scripts alone cannot judge composition or art direction.

The revision loop has hard stops: a maximum revision count, identical render detection, repeated ineffective changes, and lack of measurable progress. A user-approved visual direction must not be silently replaced.

## Quick start

Requirements: Blender with Python support; an AI agent capable of inspecting images for autonomous visual review. No Tripo, Meshy, online 3D generator, or Python package installation is required for the preview renderer.

Install `skills/ai-scene-architect/` as a skill folder in a compatible agent. Or use the scripts directly:

```bash
blender --background my_scene.blend \
  --python skills/ai-scene-architect/scripts/render_previews.py -- \
  --output ./previews --resolution 512 --engine cycles-cpu
```

The renderer writes `hero.png`, `three_quarter.png`, `top.png`, and `manifest.json`. It never saves changes back into the input `.blend` file.
Use `--engine scene` to retain the file's renderer. The `cycles-cpu` option is suitable for environments where headless Eevee cannot initialize a graphics context. Bound the Blender subprocess with an external timeout; a stalled render must not cause an endless agent run.

Have an image-capable agent inspect all three renders using the rubric in `skills/ai-scene-architect/references/visual-quality.md`, then record the review in JSON:

```json
{
  "iteration": 0,
  "visual_reviewed": true,
  "elapsed_seconds": 25,
  "change_signature": "initial-preview",
  "renders": {"hero": "paste-actual-64-character-sha256-from-manifest"},
  "issues": [
    {"id": "flat-lighting", "severity": 2, "evidence": "The foreground blends into the background", "fix": "Increase key/fill contrast"}
  ]
}
```

Replace the `renders` placeholder with the actual 64-character digest from `manifest.json`. The `visual_reviewed` flag must be set only after an agent has opened the actual images. `elapsed_seconds` is cumulative time since the run started.

Save a JSON array of reviews as `review-history.json`. After each review, check whether another revision is allowed:

```bash
python skills/ai-scene-architect/scripts/iteration_guard.py \
  --history review-history.json --max-revisions 2
```

The command outputs a machine-readable `continue` or `stop` decision with reasons. The AI should never start a revision if it returns `stop`.

## Planned next steps

1. Scene planning schema (dimensions, layout, style constraints, asset inventory).
2. Reusable Blender procedural builders and asset-library reuse.
3. Engine-specific export and verification for Godot, Unity, and web GLB.
4. Reference-image alignment and visual comparisons, with human approvals at style boundaries.

## License

MIT. See [LICENSE](LICENSE).
