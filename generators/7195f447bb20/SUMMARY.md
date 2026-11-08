# 7195f447bb20

0-bg grid (h ∈ 6-16, w ∈ 6-16, by difficulty) with: N_GAPS ∈ 1-7 PAIRS OF COLOR-4 (YELLOW) CELLS, each pair placed at (r, c) and (r+2, c+2) on a descending diagonal (SE direction), with the midpoint (r+1, c+1) intentionally LEFT AS 0 (the 'gap'). Pairs separated by 5-cell diagonal bands (used set prevents overlapping or extending into longer diagonal runs). Rule (FOR EACH PAIR OF COLOR-4 CELLS ON A DESCENDING (SE) DIAGONAL WITH OFFSET (2, 2), FILL THE MIDPOINT (R+1, C+1) WITH COLOR 4; CELLS PART OF LONGER DIAGONAL RUNS (>3) ARE NOT MODIFIED): SCAN every pair of color-4 cells. For EACH pair where one is at (r, c) and another at (r+2, c+2) AND the midpoint (r+1, c+1) is currently 0: PAINT g[r+1][c+1] = 4. The endpoints stay. Net: each diagonal pair with a gap is completed into a 3-cell SE diagonal run.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
