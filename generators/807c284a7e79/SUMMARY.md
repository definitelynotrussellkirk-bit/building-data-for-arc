# 807c284a7e79

A color-2 seed starts a four-neighbor flood through its non-8 connected component. Reached cells become color 3 at even shortest-path distance and color 4 at odd distance; color-8 walls and every unreachable zero remain unchanged.

Generator version `3.0.0` exposes four exact, pixel-recoverable controls: `grid_h` (8–12), `grid_w` (10–14), `scene_profile` (`connected`, `split_seed_small`, `split_seed_large`), and `wall_orientation` (`vertical`, `horizontal`). Every consecutive three-sample lesson cycles through all three scene profiles. This guarantees evidence against the public-example shortcuts “checkerboard every non-wall cell” and “always fill the largest chamber,” while alternating seed parity also refutes a fixed-origin checkerboard.

The first five slots of each ten-sample cycle use canonical-size anchors; remaining slots draw within the declared size envelope. Difficulty changes only the default size distribution, so explicit boundary overrides stay legal in every band. The selected canonical Racket rule remains the label authority with `RULE_HASH = 229d8e0a7e30`.

Kind: `per_puzzle`. Reviewed version: `3.0.0`.
