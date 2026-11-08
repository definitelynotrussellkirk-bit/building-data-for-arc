# 222de43cc4aa

0-background grid (h in [3, 8], w in [9, 21]) holding a DOTTED LATTICE: 1-2 foreground colors, and every row a short-period (2-4) pattern of isolated marks — single cells, sometimes domino clusters — so the grid holds many small objects (~12-35) like the canonical dotted rows (width 17, period-2 middle rows, period-4 top/bottom rows). The grid is NOT vertically symmetric, so the reflection is visible. Rule (VERTICAL PINGPONG / ZIGZAG EXTENSION): output height = 4*(h-1)+1 covering TWO full pingpong periods of 2*(h-1); output width = input width. For each output row i: pos = i mod (2*(h-1)); if pos <= h-1 the source row is input row pos, else it is input row 2*(h-1)-pos (reflection). Net: the input zigzags up-down vertically through two full reflection cycles.

Kind: `per_puzzle`. Imported version: `3.1.1`.
Approval is derived by the catalog from current code and retained evidence.
