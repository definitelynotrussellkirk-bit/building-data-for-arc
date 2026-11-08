# b1cf9bc21c63

0-bg grid (h, w~7-12) with 2-5 BLUE(1) L-TROMINOES (3-cell L-shapes in 2×2 bboxes with one MISSING CORNER) placed at non-touching anchors (min Chebyshev distance 3 between anchors). EACH tromino occupies 3 of 4 cells in its 2×2 bbox, with the missing corner randomly chosen from the 4 positions. Rule (FILL EACH 2×2 WINDOW WITH 3 BLUE + 1 BG → COMPLETE WITH RED): scan EVERY 2×2 WINDOW in the grid. For EACH window containing EXACTLY 3 BLUE(1) CELLS AND 1 BG(0) CELL: PAINT the bg cell with COLOR 2 (red). Windows with other blue counts (0, 1, 2, 4) stay unchanged. Net: each L-tromino gains a red dot in its missing corner, completing it to a blue-3 + red-1 2×2.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
