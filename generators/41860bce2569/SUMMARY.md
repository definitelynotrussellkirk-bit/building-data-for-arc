# 41860bce2569

0-bg grid (h~9-11, w~11-13) with: (a) ONE COLOR-2 (red) START CELL; (b) ONE COLOR-3 (green) GOAL CELL ≥4 Manhattan from start; (c) 0-3 COLOR-8 (cyan) WALL cells (≥2 cells from start/goal); (d) optional COLOR-4 PORTAL PAIR (2 cells at distinct positions, probability 0.5). Rule: APPLY BFS (4-conn) from RED start to GREEN goal, avoiding CYAN walls. COLOR-4/6 PORTAL PAIRS act as teleporters — entering one portal transports to the other (zero step). FIND the SHORTEST PATH. PAINT every 0-cell along that path with COLOR 8. Start, goal, walls, and portals stay. Net: output adds an orange trail of the shortest portal-aware path.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
