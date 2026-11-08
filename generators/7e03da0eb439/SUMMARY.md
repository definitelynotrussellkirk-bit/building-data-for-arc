# 7e03da0eb439

Fixed 3×3 grid (canonical input dim) with: (a) one or more TRIGGER cells set to color 2; (b) non-2 cells filled with some pattern (zero / mixed_low / mixed_full / sparse_high) from a non-2 palette. Rule: self-tile — output is 9 × 9. For each cell (R, C) of the output, let (R_tile, C_tile) = (R // 3, C // 3) and (r, c) = (R % 3, C % 3). The output cell = input[r][c] IF the tile cell input[R_tile][C_tile] == 2, else 0. Net: a 3 × 3 mosaic of 3×3 tiles — each input==2 cell gets stamped with a copy of the whole input, non-2 cells stay blank.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
