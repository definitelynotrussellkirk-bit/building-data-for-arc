# c9034f0626e0 — Exact parity-pair fill with gray blockers

Version: `3.0.0`
Canonical rule hash: `d29d80b108a0`

## Input distribution

Each input uses one of the three published canonical profiles:

- `canonical_13x13`: 13×13 with exactly 69 gray (`5`) cells;
- `canonical_13x16`: 13×16 with exactly 94 gray cells;
- `canonical_15x17`: 15×17 with exactly 81 gray cells.

A dense, fragmented gray surround leaves a large connected zero field. Exactly one non-`0`/non-`5` marker appears inside that field. The exact observable controls are `scene_profile`, `marker_color`, and `marker_parity`; every legal cross-product is supported in every difficulty band, and unknown or invalid controls are rejected. Difficulty changes gray-component morphology without narrowing the exact control domains.

## Rule

Let the marker be at `(mr, mc)` with color `M`. Replace a cell only when it is currently `0` and `(row mod 2, column mod 2) = (mr mod 2, mc mod 2)`. Fill it with `M`. Preserve the marker, every gray blocker, and every zero of the other three ordered parity classes.

## Teaching design

Every generated grid contains background witnesses in all four ordered parity classes, at least one same-parity gray blocker, and same-parity background cells. This makes each sample disagree with six plausible wrong rules: row-only parity, column-only parity, checkerboard-sum parity, fill-all-zeroes, overwrite-same-parity blockers, and identity.

Three consecutive production samples cover all three canonical profiles. The declared lesson minimum is three demonstrations. A source-bound final census over 300 lessons and all 1,200 leave-one-pair-out query rotations found no ambiguity against the six declared competitors.
