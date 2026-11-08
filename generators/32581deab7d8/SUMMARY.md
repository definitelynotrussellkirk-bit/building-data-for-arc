# 32581deab7d8

0-bg grid (h, w~12-18) with 2-4 COLOR-3 (green) SINGLE-CELL SEEDS at interior positions (edge_margin=2 from borders) separated by min_separation=6 cells. Position bias options: scattered/corners/diagonal/row_aligned/centered. Rule (BUILDING-PROFILE STAMP): for EACH GREEN SEED at (sr, sc), STAMP a 'BUILDING PROFILE' shape centered at (or anchored to) the seed. A 'building profile' is a task-specific fixed motif (e.g., a 3×3 cross, an L-shape, or a house-like silhouette) painted in COLOR 3. The stamp is CLIPPED at grid edges if it extends beyond. Multiple seeds → multiple stamps with no overlap (thanks to min_separation). Net: each green seed expands into a building-shape stamp; min_separation ensures stamps don't collide.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
