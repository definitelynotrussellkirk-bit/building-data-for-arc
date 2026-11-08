# f527b82316c1

0-bg SMALL grid (h, w ~ 3-10) with SPARSE NON-BG CELLS painted in non-{0, 8} colors drawn from a palette of 1-4 distinct colors. Cell placement follows one of 7 density patterns (sparse / medium / dense / checker / diagonal / corners / stripes) with cell counts scaled to grid area (roughly h*w/8 to h*w/2). The constraint: at least one non-bg cell; no cell uses color 8 (reserved for output). Rule (TILE 2×2 THEN PAINT DIAGONAL HALOS WITH COLOR 8): produce an OUTPUT of dimensions (2*h, 2*w) by REPLICATING the input as a 2×2 TILE GRID (output[r][c] = input[r mod h][c mod w] for all r, c). Then, for EACH 0-CELL in the tiled output: CHECK if any of its FOUR DIAGONAL NEIGHBORS (positions (r-1, c-1), (r-1, c+1), (r+1, c-1), (r+1, c+1)) contains a non-0 value. If YES: PAINT this 0-cell with COLOR 8. Otherwise stay 0. Non-bg input-tile cells stay their original color. Net: a 2×2-tiled output where each non-bg cell gets a halo of 8s painted in the 4 diagonal directions, while cardinal neighbors stay 0.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
