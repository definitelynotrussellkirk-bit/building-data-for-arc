# 3a379d1ed52c

0-bg grid (h, w~7-12) with 2-5 BLUE(1) L-TROMINOES (3-cell L-shapes in 2×2 bboxes with one missing corner). L-trominoes are placed at ANCHOR-GRID positions (every 3 cells starting at row 0, col 0), each with a RANDOM MISSING CORNER (one of 4 orientations). Each L-tromino occupies 3 of 4 cells in its 2×2 bbox, leaving the missing corner at 0. Rule (FILL EACH 2×2 WINDOW WITH 3 BLUES + 1 BG CELL → GREEN AT THE BG CELL): scan EVERY 2×2 WINDOW in the grid. For EACH window containing EXACTLY 3 BLUE(1) CELLS AND 1 BG(0) CELL: PAINT the bg cell at (r, c) with COLOR 3 (green). Windows with other blue-counts (0, 1, 2, 4) stay unchanged. Net: every L-tromino completes to a 2×2 solid by adding a green dot in the missing corner.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
