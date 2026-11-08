# 42ccd1ff25f3

0-bg grid (h~6-8, w~7-9) with exactly 3 SINGLE-CELL SEEDS in distinct colors at fixed asymmetric anchor positions: (1, 1), (1, w-2), (h-2, 3). Rule: extract seeds (all non-bg cells). For each cell of the output grid: if input is non-bg, keep that value. Else compute Manhattan distance to each seed, sort ascending; if the MIN distance is unique → take that seed's color; else (tie at the minimum) → 0. Net effect: nearest-seed Voronoi tessellation with ties left as bg.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
