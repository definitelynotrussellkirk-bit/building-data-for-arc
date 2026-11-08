# 9e0cd377fa63

0-bg grid (h, w~10-15) with 2-3 PAIRS of SAME-COLOR CORNER MARKERS — each PAIR consists of TWO cells in a DISTINCT non-0 color, placed at diagonally OPPOSITE CORNERS of an axis-aligned rectangle (both row-span ≥3 and col-span ≥3). Pair rectangles are SEPARATED (≥1-cell gap between bboxes). Rule (EXPAND EACH CORNER PAIR INTO ITS RECTANGLE PERIMETER): For EACH COLOR C appearing as exactly 2 cells at (r1, c1) and (r2, c2) (diagonally opposite corners of an implicit rectangle): PAINT the entire PERIMETER of the axis-aligned rectangle from (min(r1, r2), min(c1, c2)) to (max(r1, r2), max(c1, c2)) — i.e., all cells on the top row, bottom row, left col, right col of that bbox — with color C. Net: each pair of corner markers grows into a rectangle outline.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
