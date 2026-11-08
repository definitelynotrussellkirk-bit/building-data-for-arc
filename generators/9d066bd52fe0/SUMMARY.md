# 9d066bd52fe0

0-bg grid (h~7-9, w~8-11) with: (a) 1-2 GRAY (COLOR-5) WALLS — each wall is a near-full row or column with 1-2 GAPS (openings) at random positions; (b) 2-3 SINGLETON SEED CELLS in DISTINCT colors from {2, 3, 4, 6, 7, 8, 9} placed at BG positions with Manhattan distance ≥ max(3, min(h, w)//2) between any pair. Rule (GEODESIC VORONOI FILL AROUND GRAY WALLS): For EACH BG cell at (r, c): compute GEODESIC (4-conn, non-wall) distance to EACH SEED. PAINT the cell with the COLOR of the NEAREST seed by geodesic distance. Ties broken task-specific. Walls stay 5. Net: each connected region partitions by nearest seed (geodesic Voronoi), with walls blocking shortest paths.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
