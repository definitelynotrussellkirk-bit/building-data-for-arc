# 2abfa4e4beeb

0-bg grid (h, w ∈ 12-14) with: (a) FOUR MARKER CELLS at FIXED positions — g[0][7] = COLOR 2, g[1][10] = COLOR 3, g[2][2] = COLOR 4, g[1][0] = COLOR 6; (b) ONE COLOR-1 PLUS-SHAPED BLOB at FIXED position centered around (6, 6) — 5 cells: (5, 6), (6, 5), (6, 6), (6, 7), (7, 6) forming a +. Rule (COMPUTE TWO DELTA VECTORS: V1 = (3-MARKER POS) - (2-MARKER POS); V2 = (6-MARKER POS) - (4-MARKER POS); COMBINE V = V1 + V2; FOR EACH COLOR-1 CELL, PAINT COLOR 8 AT (R + V.R, C + V.C) IF IN-BOUNDS): LOCATE the 4 markers (one each of colors 2, 3, 4, 6). COMPUTE v1 = pos(3) - pos(2), v2 = pos(6) - pos(4). LET v = v1 + v2. For EACH color-1 cell at (r, c): COMPUTE target (r+v.r, c+v.c); IF in-bounds: PAINT g[r+v.r][c+v.c] = COLOR 8 (cyan). Original cells preserved. Net: the + blob is copied to color 8 at a translated position dictated by the 4-marker vector sum.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
