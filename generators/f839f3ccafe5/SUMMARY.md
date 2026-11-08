# f839f3ccafe5

PERIODIC-TILED grid: a random p × p TILE (p ∈ {3, 5, 7}) populated with colors from a palette of 2-4 distinct non-{0,1} colors drawn from {2..9}, then REPEATED across an h × w grid where h = p * h_factor and w = p * w_factor (h_factor, w_factor each ∈ {3, 4}, so h, w both divisible by p). After tiling, 1-3 RECTANGULAR CORRUPTION BLOCKS of size 2..5 × 2..5 are placed at positions determined by a position_bias (scattered / centered / corners / spread), and every cell inside each block is OVERWRITTEN with COLOR 1 (blue) — corrupting the periodic pattern there. Rule (DETECT THE PERIODIC TILE, RESTORE OVER COLOR-1 CELLS): find the smallest period p such that the non-1 cells obey period p in both axes (grid[r][c] = grid[r mod p][c mod p] for every non-1 cell). RECONSTRUCT the p × p tile by reading any non-1 representatives at each (r mod p, c mod p) offset. REPAINT every COLOR-1 cell with the tile's value at its (r mod p, c mod p) offset. Non-corruption cells stay unchanged. Net: the 1-block corruption vanishes, leaving a clean periodic tiling.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
