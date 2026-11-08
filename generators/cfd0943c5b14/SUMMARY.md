# cfd0943c5b14

A 6..12 by 6..12 zero-background grid contains 2..5 sparse nonzero seed cells. Every nonzero cell is a seed, including cyan (`8`). The output is a fresh zero grid in which each seed paints cyan at its own position and at its four diagonal neighbors; out-of-bounds stencil cells are clipped and overlapping stamps are unioned.

The v3 curriculum cycles through five explicit scenes: canonical interior color-3 seeds, a non-cyan edge seed, mixed cyan/non-cyan interior seeds with overlapping X footprints, a non-cyan corner seed, and cyan interior seeds. Four demonstrations are assembled from consecutive schedule slots so complete lessons challenge three canonical-fitting shortcuts: ignoring cyan seeds, ignoring boundary seeds, and treating color 3 as the only seed color.

Public exact controls are `grid_h` (6..12), `grid_w` (6..12), `seed_count` (2..5), and `scene`. The clean generated domain excludes orthogonally adjacent seeds and uses at most one boundary seed.

Kind: `per_puzzle`. Reviewed version: `3.0.0`. Canonical rule hash: `6e86df413712`.
Approval is derived by the catalog from current code and retained evidence.
