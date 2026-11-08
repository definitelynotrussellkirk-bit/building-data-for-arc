# e9000404cfef

Tiled lattice: tile_rows x tile_cols equal tiles separated by 1-cell color-9 divider rows/columns. Tile size varies (2x2/2x3/3x2/2x4/4x2/3x3, area<=9 so per-tile counts stay <=9, incl non-square). Each tile holds count (0..area) random non-0 cells in one colour. Rule: split on full-9 dividers and output a tile_rows x tile_cols grid where each cell = that tile's nonzero count. Tile size, counts (0..area), lattice dims and colours all vary.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
