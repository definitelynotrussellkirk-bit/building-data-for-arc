# 60e8a302bbab

COLOR-7 (orange) background grid (h ∈ 12-16, w ∈ 14-18) with: 1-3 SE-DIAGONAL LINES of COLOR 5 (gray) — each line is (r0, c0), (r0+1, c0+1), ..., (r0+L-1, c0+L-1) of length L ∈ 4..min(h, w)-2, placed at random top-left position with all cells starting on the 7-bg. Lines are non-overlapping (placement retries until clean). NO SW-DIAGONAL PAIRS of 5s exist by construction (only SE-diagonal lines are placed). Rule (COUNT SE-DIAGONAL VS SW-DIAGONAL ADJACENT 5-PAIRS; RECOLOR THE WINNING DIRECTION'S LINES TO COLOR 8, OTHER TO COLOR 2): SCAN every pair of diagonally-adjacent 5-cells. COUNT n_SE = pairs where (r1, c1) and (r1+1, c1+1) are both 5. COUNT n_SW = pairs where (r1, c1) and (r1+1, c1-1) are both 5. IF n_SE > n_SW: RECOLOR every 5 cell on an SE-diagonal line to COLOR 8 (cyan), and every 5 cell on a non-SE diagonal (SW) to COLOR 2 (red). ELSE: swap (SW→8, SE→2). Net: winning-direction lines become cyan, losing-direction lines become red, on the orange background.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
