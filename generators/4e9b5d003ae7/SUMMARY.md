# 4e9b5d003ae7

0-bg grid with exactly one full color-3 row at cross_row and one full color-3 column at cross_col forming a green '+' cross. The cross divides the grid into 4 quadrants. Rule: each quadrant anchor is the inner corner adjacent to the cross. For each non-cross cell (r, c), compute Chebyshev distance from anchor: if dist is ODD → color 4, else → 0. Cross cells (color 3) preserved. Output is 4 quadrants filled with concentric alternating 4/0 rectangles centered on the cross corner.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
