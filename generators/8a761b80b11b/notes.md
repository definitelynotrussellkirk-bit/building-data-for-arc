# Working notes: 8a761b80b11b

## 2026-10-26 repair and parametric build

- Removed four dead declared controls and now rejects unknown overrides.
- Explicit legal dimensions work under `easy`, `medium`, `hard`, and no
  difficulty; ordinary generation places the exact requested run count.
- Palette choice affects actual run colors. Degenerate textures honor dimensions
  and reject irrelevant palette/run-count controls.
- Added an exact-default `endpoints | longest_color_gate` native family. The
  nondefault setting first selects the unique longest run's color, then uses
  that intermediate to choose endpoint versus center projection per run.
- Two demonstrations distinguish the supported setting from canonical,
  first-run-anchor, and all-centers executable rivals. Protected-Racket tests,
  authoring preflight, wrong-anchor causal replay, finite-rival self-review, and
  single-query public projection all pass.
- Owner source review, native qualification/acceptance, and training admission
  remain pending.
