# 22b4e6220898

0-bg grid (h~8-12, w~9-14) with 2-4 PAIRS of ENDPOINT CELLS, each pair in a DISTINCT color from {1..9}\{0, 8}. Each pair: two cells at random positions with row delta ≥ 2 AND col delta ≥ 2 (forces non-trivial L-paths). Endpoints don't reuse cells across pairs. Rule (DRAW HORIZONTAL-FIRST L-PATH PER PAIR, MARK OVERLAPS WITH 8): For EACH ENDPOINT PAIR (ar, ac), (br, bc): DRAW an L-PATH horizontal first then vertical (or task-specific) — paint every cell along the path in the pair's color. After drawing all paths: for EACH cell visited by ≥2 paths, REPAINT in COLOR-8 (cyan). Net: L-routed paths between each endpoint pair; path intersections become cyan.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
