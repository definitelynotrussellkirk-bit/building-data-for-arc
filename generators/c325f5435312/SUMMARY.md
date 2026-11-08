# c325f5435312

0-bg grid (h~9-13, w~9-14) with 2-3 RECTANGLE-CORNER PAIRS — for each rect: 2 same-color cells placed at DIAGONALLY OPPOSITE CORNERS of an implied axis-aligned rectangle (either main-diagonal (r0,c0)+(r1,c1) or anti-diagonal (r0,c1)+(r1,c0)). Each pair uses a DISTINCT color (2-3 colors total). Implied rects are 3..5 rows × 3..6 cols, with 1-cell buffer between rects (no overlap). Rule: for EACH PAIR of SAME-COLOR CELLS, INTERPRET them as DIAGONALLY OPPOSITE CORNERS of an axis-aligned rectangle. FILL the entire rectangle interior (all cells in (min_r..max_r) × (min_c..max_c)) with the pair's COLOR. Net: each diagonal corner pair becomes a filled rectangle in its color.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
