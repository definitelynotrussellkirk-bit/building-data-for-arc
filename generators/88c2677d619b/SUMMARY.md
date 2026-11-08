# 88c2677d619b

Grid (h~8-12, w~11-16) with a color-5 (gray) outer border, a vertical middle WALL (with one gap), a horizontal half-wall on the left half. Three single-cell SEEDS in colors 1, 2, 3 placed in distinct interior cells. Rule: for each seed s ∈ {1,2,3}, compute BFS distance d_s from that seed (treating color-5 cells as walls). For each open cell (r, c): find the seed with MINIMUM distance — paint with that seed's color. If the minimum is achieved by ≥2 seeds (tie), leave as 0 (ambiguous nearest).

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
