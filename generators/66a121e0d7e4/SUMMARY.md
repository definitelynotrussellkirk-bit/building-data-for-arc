# 66a121e0d7e4

0-bg grid (h~7-10, w~8-12) with: (a) COMMAND CELL at (0, 0) painted with value cmd ∈ {1..4} encoding transform (1=identity / 2=flip / 3=rot-CW / 4=rot-180); (b) ROW SELECTOR MARKERS — COLOR 8 cells in column 0 at rows from a fixed set [2, 4, 6] (3 row indices); (c) COLUMN SELECTOR MARKERS — COLOR 8 cells in row 0 at columns [2, 4] (2 col indices); (d) SUBMATRIX CELLS — at every (r, c) with r in row-selectors and c in col-selectors, a cell painted in a non-{0, 8, cmd} color (cycled from palette). The 8-markers define the submatrix rows × cols. Rule (READ ROW/COL SELECTORS, EXTRACT THE SUBMATRIX, APPLY CMD TRANSFORM): READ the SELECTORS — row indices R (cells in col 0 with value 8) and col indices C (cells in row 0 with value 8). EXTRACT the |R| × |C| SUBMATRIX from positions (R[i], C[j]). READ the CMD at (0, 0) and APPLY the corresponding TRANSFORM (identity / flip / rot-CW / rot-180). OUTPUT the transformed submatrix. Net: the submatrix picked by 8-markers is transformed per the (0, 0) cmd.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
