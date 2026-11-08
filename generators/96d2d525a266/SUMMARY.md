# 96d2d525a266

On a background-0 grid, process nonzero colors in row-major first-occurrence order. A color qualifies only when it occurs exactly twice and the two cells use distinct rows and columns; paint that pair's bounding-box outline in the color. Ignore singletons, aligned exact pairs, and colors with three or more cells. Outlines may overlap and overwrite any existing cell, so first-occurrence order can change the final answer.

The repaired sampler exposes four exact axes (`grid_h`, `grid_w`, `n_pair_colors`, and `n_decoy_colors`) and alternates a declared two-slot teaching schedule. Decoy-control slots protect observable aligned-pair and multi-cell counterexamples. Interaction-control slots guarantee overlapping order-sensitive rectangles and an outline-overwrite witness. Exact overrides retain the full advertised boundary, including zero decoys.

Kind: `per_puzzle`. Reviewed generator version: `4.0.0`. Canonical rule hash: `c060c7f67bbd`.
