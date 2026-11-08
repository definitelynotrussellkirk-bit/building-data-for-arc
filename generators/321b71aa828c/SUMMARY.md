# 321b71aa828c

0-bg grid (h~10-12, w~12-14) with: (a) MARKER GRID — 4 singleton cells in DISTINCT non-{0, 1} colors at positions (0, 0), (0, 2), (2, 0), (2, 2) (top-left 2×2 marker matrix); (b) 4 COLOR-1 (blue) SHAPES — each a 3-cell L-tromino variant placed in a 2×2 LAYOUT at anchors (4, 4), (4, 9), (7, 4), (7, 9). Rule (RECOLOR EACH SHAPE BY ITS POSITIONAL MARKER): compute SORTED UNIQUE ROWS/COLS of MARKERS (marker_rows = [0, 2], marker_cols = [0, 2]) and SORTED UNIQUE ROWS/COLS of SHAPE BBOX TOP-LEFTS (obj_rows = [4, 7], obj_cols = [4, 9]). For EACH BLUE SHAPE at top-left (R, C): find ri = obj_rows.index(R), ci = obj_cols.index(C). LOOK UP MARKER COLOR at marker[marker_rows[ri]][marker_cols[ci]]. RECOLOR all cells of the blue shape to that marker color. Markers stay. Net: shapes inherit colors from the top-left marker grid by their relative (row, col) position.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
