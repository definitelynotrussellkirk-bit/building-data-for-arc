# 3f600d3093b8

0-bg grid (h~8-12, w~8-12) with: (a) ROW MARKERS — n_row_markers (2-4) COLOR-8 cells placed at random rows r ∈ [1, h-1] in column 0 (cell (r, 0) = 8); (b) COLUMN MARKERS — n_col_markers (2-4) COLOR-8 cells placed at random columns c ∈ [1, w-1] in row 0 (cell (0, c) = 8); (c) INTERIOR — for EACH cell (r, c) with r ≥ 1 and c ≥ 1: independently fill with a random non-{0, 8} color from a 4-color palette at density 0.5. Cell (0, 0) stays bg-0. Rule (EXTRACT THE SUB-MATRIX OF MARKED ROWS AND MARKED COLUMNS): READ the ROW MARKERS — the set R of row indices r where g[r][0] = 8. READ the COLUMN MARKERS — the set C of column indices c where g[0][c] = 8. PRODUCE an OUTPUT grid of size |R| × |C| where output[i][j] = g[R[i]][C[j]] (cell at the intersection of the i-th marked row and the j-th marked column, sorted ascending). The marker cells themselves and unmarked rows/cols are dropped. Net: a tiny sub-matrix of the interior, sampled at the marker-indicated rows × columns.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
