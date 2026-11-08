# bd2a79b78c01

0-bg grid (h~10-14, w~11-16) with: (a) a RADIUS INDICATOR at (0, 0) = value in {1, 3} (encoding radius 1, 2, or 3); (b) a VERTICAL COLOR-5 (gray) WALL at random col wall_col (4..w-5) with ONE GAP at row gap (3..h-3); plus a partial HORIZONTAL gray wall at row h-3 with select gap columns; (c) a CONNECTED L-SHAPED COLOR-2 (red) SEED of 3 cells in the lower-left chamber. Rule (DILATE RED SEED BY TOP-ROW RADIUS THROUGH NON-WALLS, PAINT CYAN): identify RADIUS R from (0, 0). DILATE the RED SEED COMPONENT by R cells through 4-connected non-5 (wall) cells (BFS depth ≤ R from any seed cell). PAINT all reached non-seed cells with COLOR-8 (cyan). The radius indicator, walls, and seed stay. Net: red seed grows cyan halo of radius R, blocked by gray walls.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
