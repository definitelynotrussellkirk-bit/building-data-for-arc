# 258e1a721c75

0-bg grid (h~9-11, w~12-14) with: (a) ROW 0 = PALETTE — 3 distinct non-{0, 2} cells scattered at distinct columns of row 0, in their natural left-to-right order; (b) BELOW row 0: exactly 3 isolated 4-connected COMPONENTS all in color 2 (red), each a 3-4 cell motif with distinct leftmost columns. Rule: extract palette = row 0 non-{0,2} values in scan order (left to right). Extract color-2 components, sort by (leftmost_col asc, then top row asc). For each component in sorted order, recolor its cells to the corresponding palette color (1st component → 1st palette color, etc.). Row 0 cells preserved.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
