# d7b74143cb92

0-bg grid (h~9-13, w~12-17) with COLOR-5 (gray) WALLS: (a) FULL-HEIGHT VERTICAL WALL at col w//2 with a GAP at random row (in 3..h-4); (b) SHORT HORIZONTAL WALLS at row h//2 scattered on both sides at random columns (random True/False); This creates 2 CHAMBERS. THREE SEEDS placed at fixed corners: COLOR-4 at (1, wall_col-2), COLOR-3 at (h-2, 2), COLOR-2 at (h-2, w-3). Rule (WALL-AWARE VORONOI + TIE MAP): for EACH 0-CELL, compute the SHORTEST BFS DISTANCE to each of the 3 SEEDS through walkable (non-5) cells. If one seed is strictly closest, MAP its color to {2 → 6, 3 → 7, 4 → 8}. If MULTIPLE seeds tie for closest, MAP to COLOR 9. Unreachable cells (separated by walls) get COLOR 9 or 0. Net: 3-seed wall-aware Voronoi, ties = 9.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
