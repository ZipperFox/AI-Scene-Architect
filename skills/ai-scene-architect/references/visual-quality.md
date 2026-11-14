# Visual Quality Review

The AI's job is to critique the rendered outcome, **not** to invent detail until the screen looks busy. Use the user's intended visual identity and game function as primary references. Treat generic commercial AI-style polish as an anti-goal unless explicitly requested.

## Evaluate in this order

1. **Art direction** — Does the result match the user-selected genre, historical era, target stylization, palette, and references? Record a mismatch before any lighting tweak.
2. **Composition** — Is there a deliberate hierarchy of foreground, midground, background, and focal point? Is the most important gameplay silhouette readable?
3. **Proportions** — Do objects have coherent real or stylized scale, convincing construction, contact with the ground, and useful negative space?
4. **Materials** — Check plastic shine, excessive uniform bevels, unnaturally even edge wear, repetitive procedural noise, and identical material response on unrelated surfaces. Texture noise is not artistic quality.
5. **Lighting and color** — Check scene-dependent key/fill/rim choices, overexposure, crushed blacks, unwanted color casts, and lack of subject/background separation. Do not universally prescribe cinematic bloom or contrast.
6. **Game use** — Check player navigation, cover/occlusion, collision intent, draw-call/texture/mesh budgets, and target camera distance where applicable.

## Evidence format

Every review is one JSON object. Keep issue IDs stable between reviews, e.g. `material-plastic-wood`, `layout-blocked-path`, `lighting-flat`.

```json
{
  "iteration": 1,
  "visual_reviewed": true,
  "change_signature": "lighting:move-key-left",
  "renders": {
    "hero": "sha256-hex-of-rendered-file",
    "three_quarter": "sha256-hex-of-rendered-file",
    "top": "sha256-hex-of-rendered-file"
  },
  "issues": [
    {
      "id": "lighting-flat",
      "severity": 1,
      "evidence": "The hero view still has weak subject/background separation",
      "fix": "Increase the key-to-fill ratio without crushing the cave entrance"
    }
  ]
}
```

Severity: 1 = minor polish, 2 = noticeable quality issue, 3 = serious defect or violation. Record only visible issues supported by inspected images. If the rendered image contains nothing usable, report failure rather than an aesthetic rating.

## Review loop

1. Render a baseline: `iteration: 0`.
2. Open all generated images, state the highest-impact issues and evidence, and write a review record.
3. Run `iteration_guard.py` on the cumulative JSON array **before** the next revision.
4. If allowed, fix one issue cluster using the smallest meaningful edit, render again, and compare against baseline and previous version.
5. Report no-progress or identical-render observations as warnings, but use the revision count as the only iteration limit (default 2 changes). Stop early if the target quality is met or a proposed change violates an approved constraint. Report unresolved issues honestly.

### Important limitation

There is no universal objective detector for an "AI-looking" scene. A vision-capable model can provide structured critique, but its judgement may vary. Use approved reference images, concrete visible evidence, and optional human review to prevent aesthetic drift.
