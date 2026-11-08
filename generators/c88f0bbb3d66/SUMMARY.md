# c88f0bbb3d66

0-bg grid assembled from N=3-4 SIDE-BY-SIDE PANELS (each h×w ~ 5-6 × 5-6) separated by FULL COLOR-9 (maroon) COLUMNS of width 1. Each panel is filled with cells in a DISTINCT panel color (2, 3, 4, …): 3-5 SHARED cells appear in ≥2 panels (threshold-2 overlap positions), plus 3 panel-unique cells. Rule (MAJORITY-VOTE MASK AT THRESHOLD 2): identify the N PANELS (separated by 9-rows). For EACH INTERIOR (r, c), COUNT how many PANELS have a non-0 cell at (r, c). EMIT an h×w MASK where out[r][c] = 8 (cyan) if COUNT ≥ 2, else 0. Net: cells lit in ≥2 panels form an 8-mask.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
