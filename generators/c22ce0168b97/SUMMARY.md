# c22ce0168b97

0-bg grid (h, w~6-10) with: (a) TOP ROW (row 0) containing 2-5 COLOR HEADERS at random distinct columns, in DISTINCT non-{0, 8} colors; (b) BODY (rows 1..h-1) with 1-3 COLOR-8 MARKER CELLS in each header column at random rows. Columns without headers stay 0. Rule (HEADER-DIRECTED RECOLOR): for EACH COLUMN c where row 0 contains a NON-ZERO HEADER COLOR header_c, find all body cells in that column with value 8 and RECOLOR them to header_c. The top-row header stays. Cells in header-less columns and non-8 body cells stay. Net: top-row color tags propagate down their column to repaint every 8-marker.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
