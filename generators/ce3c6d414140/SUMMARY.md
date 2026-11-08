# ce3c6d414140

0-bg grid (h, w ~10-16) with 1-3 HOLLOW PARALLELOGRAM shapes — each outlined as a top row, a left slanted edge, a right slanted edge, and a bottom row. Each shape uses a single non-bg color. Shapes are isolated by ≥1 bg cell (no touching). Rule: extract 8-connected objects. For each object, mark 'stay' cells = those on the BOTTOM ROW or RIGHTMOST COL of the object's bbox. For each cell (r, c) in the grid: if it's a stay cell, keep its original value. Else if (c > 0) AND input[r][c-1] is non-zero AND input[r][c-1] is NOT a stay cell → copy input[r][c-1] (shift right). Else 0. Net effect: the top and left edges of each parallelogram shift RIGHT by 1 cell; bottom and right edges stay in place.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
