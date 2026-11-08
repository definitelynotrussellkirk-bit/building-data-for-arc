# a8ac6887ee58

0-bg grid (h~5-7, w~7-9) with: (a) ONE COLOR-3 (green) CELL at (r3, c3); (b) ONE COLOR-4 (yellow) CELL at (r4, c4). Cells are placed so Manhattan distance ≥ min_separation (2-4) and direction (relative placement) is one of 8 cardinal/diagonal directions (n/s/e/w/nw/ne/sw/se). No other cells. Rule (SHIFT COLOR-3 ONE STEP TOWARD COLOR-4): identify the 3-cell at (r3, c3) and the 4-cell at (r4, c4). COMPUTE delta = (sign(r4 - r3), sign(c4 - c3)). ERASE the 3-cell (g[r3][c3] = 0). PLACE the 3-cell at (r3 + dr, c3 + dc) (one step toward the 4-cell). The 4-cell stays. Net: green cell takes one step toward the yellow target.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
