# AI Scene Architect

An open-source [Agent Skill](https://agentskills.io/) for AI-directed Blender scene creation, visual review, and controlled iteration.

**Current status: v0.3 visual-quality validation (draft, mixed art results).** An AI agent researches and designs scenes; reusable Blender builders assemble editable .blend/GLB, then actual renders are reviewed with a bounded correction journal. Python does not contain a text-understanding model or keyword-to-template scene selector. The v0.1/v0.2/Reference Scout foundations remain.

PR dependency chain: **PR #1 → PR #2 → PR #3 (Reference Scout) → v0.3 draft**. Review v0.3 against `feat/ai-reference-scout`. The base PRs remain unmerged; this draft does not merge them or modify main.

## v0.3: visible changes, with a recorded failure

The two Scout proposals were actually modeled and rendered in independent new
runs. [The comparison report](evidence/v03/REPORT_ZH.md) includes all six final
authored views, original-before/new-after boards, editable .blend/GLB and executed
Windows Blender checks. Hero cameras, 768px resolution, 48 samples and AgX match
the originals; the mine's secondary inspection camera changed and is labeled.

- **Woodwork shop:** improved window light, long-grain workbench with vise/open
  dog holes/plane, quieter plaster, timber flooring and unobstructed furniture.
  AI visual assessment: **PASS_WITH_WARNINGS**, user acceptance remains open.
- **Crystal mine:** connected rock shell and improved visibility, but broad
  tapered cut edges, awkward rock/timber relationships and an over-warm final
  atmosphere remain. AI visual assessment: **FAIL** for the complete art brief;
  two corrections were used and the scene was stopped, not quietly reset.

This validates real implementation and one observed visual improvement. It does
not prove that Reference Scout alone caused the gain, or guarantees better art.
Technical checks passed for both final exports; those results do not override
the mine's unresolved visual and layout issues. Old v0.2 evidence is unchanged.

## AI Reference Scout (draft extension, stacked on PR #2)

The AI designs from its own aesthetic judgement. Before a new plan/build, it
researches with whatever search/page/image tools its agent has, forms an original
Art Direction Brief, and records the inspirations it accepted, transformed or
rejected. Real-world, fantasy and science-fiction references are all valid;
research does not enforce realism or require a citation for every artistic choice.
Creative freedom does not waive quality: the AI must critique likely risks,
inspect actual rendered results and report unresolved visual failures at the
correction limit. Schema/test success alone is never aesthetic acceptance.

The [Scout workflow](skills/ai-scene-architect/references/reference-scout.md)
has no provider SDK, model binding or fixed scene keyword table. The agent derives
adaptive questions/queries; Python validates and packages the resulting data.
Sources record categories, real/fictional domain, short observations and locators,
access failures, exact URLs, license status/scope and reference use. Fictional
designs are separated from physical facts. Web content stays untrusted data and
is never executed or treated as agent instructions. No external models, textures
or artworks are imported into scenes by Scout.

```powershell
# Ask the agent to research this brief（讓代理依需求自主研究）
python skills/ai-scene-architect/scripts/reference_scout.py prepare --brief examples/crystal-mine/brief.txt --output new-scout-request.md
# After actual research, compile the AI-authored dossier（實際研究後整理資料）
python skills/ai-scene-architect/scripts/reference_scout.py compile --input researched-dossier.json --output research-01
python skills/ai-scene-architect/scripts/prepare_planning.py --brief examples/crystal-mine/brief.txt --references research-01 --output new-planning-request.md
# Bind the completed AI-authored plan, preserving its source（綁定研究與設計選擇）
python skills/ai-scene-architect/scripts/reference_scout.py bind --plan proposed-plan.json --bundle research-01 --output research-01/scene_plan.json
```

If search is unavailable, use `reference_scout.py offline --brief <file> --reason
<actual reason> --output <new directory>`. It records zero searches, explicit gaps
and local reference options; the AI can still design creatively, without faking
research. The intake clearly leaves aesthetic synthesis pending for the agent.

Actual examples: [crystal mine](examples/reference-scout/crystal-mine/art_direction_brief.md)
and [woodwork shop](examples/reference-scout/woodwork-shop/art_direction_brief.md),
with manifests and bound scene plans beside each brief. See the
[Reference Scout report](evidence/reference-scout/REPORT_ZH.md) for real sources,
tests and limits. These are researched planning proposals; they do not reopen
the stopped v0.2 scene journals. Existing two-correction/no-total-time rules remain.

## Text brief → scene plan → editable scene

Use an image-capable AI agent with [SKILL.md](skills/ai-scene-architect/SKILL.md).
The agent reads the actual brief and [planning contract](skills/ai-scene-architect/references/scene-planning.md), then authors `scene_plan.json` against the [JSON Schema](skills/ai-scene-architect/references/scene-plan.schema.json). The example plans are two independently authored demonstrations, not runtime templates.

```powershell
# Optional: prepare a request for your AI agent（產生給 AI 的規劃請求）
python skills/ai-scene-architect/scripts/prepare_planning.py --brief examples/crystal-mine/brief.txt --output planning-request.md
# Validate an AI-authored plan（驗證 AI 撰寫的規劃）
python skills/ai-scene-architect/scripts/scene_plan.py examples/crystal-mine/scene_plan.json
# Use your EXISTING Blender executable and a NEW output directory（既有 Blender、新輸出目錄）
python skills/ai-scene-architect/scripts/run_scene.py --blender 'D:/SteamLibrary/steamapps/common/Blender/blender.exe' --plan examples/crystal-mine/scene_plan.json --output output/my-mine-01
```

The pipeline creates `scene.blend`, `scene.glb`, the source plan and generator snapshot, three authored PNGs/manifest, fresh-process verification JSON, and three relit GLB diagnostic previews. It refuses existing output directories. Inspect the images, append a review via `review_history.py`, and consult the existing guard before any correction. Corrections use `--revision 1` or `2` with the **same** `--history`; do not reset it.

Builders cover ground/walls, irregular rocks/continuous relief walls, timber members/braced frames, pointed crystals, planked tables/benches/crates, and assembled minecarts/winches. Materials provide portable PBR factors plus Blender-native procedural bump. GLB does not preserve procedural bump, area lights or world lighting; relight it in the destination engine. Layout/support checks flag candidates and do not replace visual inspection or a collision solver.

Examples: [fantasy crystal mine](examples/crystal-mine/scene_plan.json) and [woodwork shop](examples/woodwork-shop/scene_plan.json). See [Windows Blender 5.3.0 validation](evidence/v02/REPORT_ZH.md) for actual renders, checks and remaining cave-art limitations. Blender 5.2.3 was not tested.

## Tests

```powershell
python -m unittest discover -s tests -v
& 'D:/SteamLibrary/steamapps/common/Blender/blender.exe' --background --factory-startup --python-exit-code 1 --python tests/blender_contract_checks.py
```

No pip installation is needed. Tests cover the v0.1 policy, plan/schema relations, review journal boundaries and Blender builder dimensions/topology/reuse. Visual quality remains an image review, not a unit-test score.

## What makes it different

The skill requires an agent to *look at actual renders*, identify concrete visual problems, make targeted changes, and compare the next render to the previous one. Rendering a PNG is not the same as evaluating its quality. The AI agent must have image-viewing capability; scripts alone cannot judge composition or art direction.

The **only configurable iteration limit is the revision count** (default: two changes after the first render). Identical renders or ineffective changes are reported as warnings, not independent stopping conditions. A user-approved visual direction must not be silently replaced.

## Quick start

Requirements: Blender with Python support; an AI agent capable of inspecting images for autonomous visual review. No Tripo, Meshy, online 3D generator, or Python package installation is required for the preview renderer.

Install `skills/ai-scene-architect/` as a skill folder in a compatible agent. Or use the scripts directly:

```bash
blender --background my_scene.blend \
  --python skills/ai-scene-architect/scripts/render_previews.py -- \
  --output ./previews --resolution 512 --engine cycles-cpu
```

The renderer writes `hero.png`, `three_quarter.png`, `top.png`, and `manifest.json`. It never saves changes back into the input `.blend` file.
Use `--engine scene` to retain the file's renderer. The `cycles-cpu` option is suitable for environments where headless Eevee cannot initialize a graphics context.

Have an image-capable agent inspect all three renders using the rubric in `skills/ai-scene-architect/references/visual-quality.md`, then record the review in JSON:

```json
{
  "iteration": 0,
  "visual_reviewed": true,
  "change_signature": "initial-preview",
  "renders": {"hero": "paste-actual-64-character-sha256-from-manifest"},
  "issues": [
    {"id": "flat-lighting", "severity": 2, "evidence": "The foreground blends into the background", "fix": "Increase key/fill contrast"}
  ]
}
```

Replace the `renders` placeholder with the actual 64-character digest from `manifest.json`. The `visual_reviewed` flag must be set only after an agent has opened the actual images. There is no total elapsed-time limit.

Save a JSON array of reviews as `review-history.json`. After each review, check whether another revision is allowed:

```bash
python skills/ai-scene-architect/scripts/iteration_guard.py \
  --history review-history.json --max-revisions 2
```

The command outputs a machine-readable `continue` or `stop` decision with reasons. The AI should never start a revision if it returns `stop`. Identical-output and no-progress warnings remain informational; they do not consume additional revisions or cause an early stop.

## Possible next steps

1. Continuous tunnel/organic enclosure builders and more furniture families.
2. Portable texture baking and packed UV layouts; asset-library ingestion.
3. Engine-specific verification for Godot, Unity, and web GLB.
4. Surface-aware contact/collision checks and reference-aligned visual comparisons.

## License

MIT. See [LICENSE](LICENSE).
