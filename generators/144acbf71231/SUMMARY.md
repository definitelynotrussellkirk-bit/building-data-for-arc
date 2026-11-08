# 144acbf71231

0-bg grid (h, w ~9-14) with 1-3 SOLID rectangles in color 1 (blue), each at least 3×3, axis-aligned, non-overlapping (separated by background). Rule: for each color-1 4-conn object, for each cell (r, c) of that object with r STRICTLY between obj_r1 and obj_r2 AND c STRICTLY between obj_c1 and obj_c2 (i.e. interior cell, not on the bbox edge), clear it to 0. Net: every solid blue rectangle becomes a hollow BORDER (1-cell-thick ring), interior becomes bg. Edge cells of the rectangle stay 1.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
