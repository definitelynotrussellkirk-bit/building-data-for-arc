# d060b09e8dbe

0-bg grid (h~7-9, w~8-10) with: (a) TWO MULTI-CELL BLOBS — an L-tromino [(0,0),(1,0),(1,1)] in upper-left area (rows 0-1, cols 0-2) in palette[0]; and a 2-cell horizontal bar [(0,0),(0,1)] in middle-right area (rows 2-4, cols w-4..w-3) in palette[1]; (b) TWO ISOLATED SINGLETONS — one in the bottom-left corner (row h-1, cols 0-1) in palette[2]; another in the middle-left interior (rows 2..h-3, cols 2-3) in palette[3]. The 4 colors are distinct non-{0} values from {2..9}. Rule (KEEP ONLY NON-BG CELLS THAT HAVE AT LEAST ONE SAME-COLOR CARDINAL NEIGHBOR — ERASE SINGLETONS): for EACH cell (r, c) with value v ≠ 0: CHECK its 4 CARDINAL NEIGHBORS. IF at least ONE neighbor also = v: KEEP the cell (stays color v). IF NONE of the neighbors = v (cell is isolated by color): SET the cell to bg-0. Net: multi-cell same-color blobs survive intact; isolated singletons are erased to bg-0.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
