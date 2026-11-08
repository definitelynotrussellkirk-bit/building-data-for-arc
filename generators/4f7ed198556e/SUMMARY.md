# 4f7ed198556e

FIXED 3×3 input grid with 1-8 COLOR-5 TRIGGER cells at positions chosen by one of 8 LAYOUTS (random/cluster/border/row/column/corners/cross/diagonal). Non-trigger cells filled by FILLER PATTERN (zero/sparse_decoy at 30%/mixed_decoy at 60%) using decoy colors from {3, 4, 6, 7, 8, 9} (excluding {0, 1, 2, 5}). Rule (STAMP 2×2 [[1, 2], [2, 1]] CHECKER AT EACH COLOR-5 TRIGGER): EMIT a 6×6 OUTPUT GRID (input doubled). For EACH cell (r, c) in the 3×3 input where g[r][c] == 5: STAMP the 2×2 CHECKER [[1, 2], [2, 1]] at output position (2r, 2c). Non-5 input cells produce 0 in the output 2×2 block. Net: each color-5 cell expands to a 2×2 checker; output is 6×6.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
