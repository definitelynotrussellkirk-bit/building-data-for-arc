# 4b9daa75c457

0-bg grid (h~6-8, w~8-10) with: (a) EXACTLY ONE color-2 (red) START cell at a random position; (b) EXACTLY ONE color-4 (yellow) WAYPOINT cell, Manhattan-distance ≥ 2 from the start; (c) EXACTLY ONE color-3 (green) GOAL cell, ≥ 2 from waypoint and ≥ 4 from start; (d) 0-8 color-5 (gray) WALL cells sprinkled to obstruct simple paths. Rule: run a 4-connected BFS shortest-path from START to WAYPOINT through 0-cells (walls and non-bg block); then from WAYPOINT to GOAL the same way. CONCATENATE the two path segments. PAINT every cell on the combined path (excluding endpoints) with color 8 (cyan). Start, waypoint, goal, and walls stay. Net: cyan trail from start → waypoint → goal, routing around gray walls.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
