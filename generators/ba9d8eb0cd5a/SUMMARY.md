# ba9d8eb0cd5a

Each row's nonzero cells are packed left while preserving their original order.

Kind: `per_puzzle`. Selected version: `2.0.0`.

The selected sampler exposes only three exact, pixel-observable controls:
`grid_h` (4..12), `grid_w` (7..16), and `n_colors` (2..9). Every generated
instance contains a row that must move, an active row already touching the left
edge, and a non-monotone row that refutes a sort-then-pack shortcut. A weighted
canonical-scale component covers the authoritative 4x9, 5x8, and 6x7 profiles
without replaying canonical grids.

Focused regression tests are under `tests/`. The reproducible 100-draw-per-band
distribution/semantic probe is `workspace/coverage_probe.py`.
Approval remains derived by the catalog from current code and retained evidence.
