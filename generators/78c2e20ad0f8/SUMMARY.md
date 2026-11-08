# 78c2e20ad0f8

Grid (h, w~6-8) with: (a) COLOR-8 (cyan) OUTER WALL — full border of color 8; (b) OPTIONAL INTERIOR WALLS by LAYOUT: none (single room), vertical (full-height color-8 column at random interior col), horizontal (full-width color-8 row), or cross (both a horizontal + vertical wall dividing into 4 rooms); (c) COLORED SEEDS — 2-3 seeds per room placed at random interior cells in DISTINCT non-{0, 8} colors. Rule (BFS FLOOD: EACH 0-CELL GOES TO ITS NEAREST SEED'S COLOR, BLOCKED BY 8-WALLS): For EACH bg-0 cell in any room: compute BFS DISTANCES (through 0-cells blocked by 8-walls) to ALL SEEDS in that room. ASSIGN the cell to its NEAREST seed's color. PAINT it with that color. Seeds and walls stay. Net: each room partitions into Voronoi-like regions colored by nearest seed.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
