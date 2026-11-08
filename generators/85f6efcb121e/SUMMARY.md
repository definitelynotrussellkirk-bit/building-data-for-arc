# 85f6efcb121e

0-bg grid (h~7-11, w~7-11) with 2-4 ISOLATED THREE-CELL GRAY (color 5) L-SHAPES placed at non-touching positions (3-cell pairwise minimum separation). Each L-shape is a 2×2 window with EXACTLY 3 of the 4 cells painted in COLOR 5 and the fourth (missing) corner left as bg-0. The missing corner is chosen uniformly at random from {(0,0), (0,1), (1,0), (1,1)}. All shapes use the same gray color 5 (palette_size=1). If random placement fails entirely, a single fallback L is drawn at (0,0)-(1,1). Rule (COMPLETE EACH THREE-CELL GRAY L-SHAPE INTO A FULL 2×2 MONOCHROME BLOCK): for EACH 2×2 WINDOW with exactly 3 color-5 cells and 1 bg-0 cell: RECOLOR the missing-corner 0 cell to COLOR 5, closing the 2×2 monochrome block. Other cells (already 5, or outside any active 2×2 window) stay unchanged. Net: every gray L-triomino becomes a solid 2×2 gray block.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
