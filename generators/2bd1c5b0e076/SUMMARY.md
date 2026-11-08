# 2bd1c5b0e076

0-bg grid (h ∈ 7-9, w ∈ 9-11) with: (a) ROW 0 markers at FIXED cols — g[0][3] = g[0][6] = 1 (COLOR-1 BLUE markers in cols 3, 6); g[0][4] = g[0][7] = 2 (COLOR-2 RED markers in cols 4, 7); (b) COL 0 markers at FIXED rows — g[1][0] = g[2][0] = 2 (red markers in rows 1, 2); g[3][0] = g[4][0] = 1 (blue markers in rows 3, 4); (c) ONE COLOR-6 (MAGENTA) DECORATION at (h-1, w-1). Rule (PAINT 3 AT INTERSECTIONS OF BLUE ROWS WITH BLUE COLS, PAINT 8 AT INTERSECTIONS OF RED ROWS WITH RED COLS): READ row 0 to extract BLUE_COLS = cols where g[0][c] == 1, RED_COLS = cols where g[0][c] == 2. READ col 0 to extract BLUE_ROWS = rows where g[r][0] == 1, RED_ROWS = rows where g[r][0] == 2. For EACH (br, bc) ∈ BLUE_ROWS × BLUE_COLS: PAINT g[br][bc] = COLOR 3 (green). For EACH (rr, rc) ∈ RED_ROWS × RED_COLS: PAINT g[rr][rc] = COLOR 8 (cyan). Net: same-color borders project intersections in distinct colors — blue×blue → green, red×red → cyan.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
