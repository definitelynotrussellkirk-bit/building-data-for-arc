# d0663a6fe440

Color-5 (gray) WALL-FILLED grid (h~7-12, w~8-14) with a CORRIDOR of passable 0-cells carved through, with one COLOR-2 (red) START cell at one end and one COLOR-3 (green) GOAL cell at the other end. Corridor topology varies: straight horizontal, straight vertical, L-bend (h-then-v or v-then-h), or 2-route rectangle PERIMETER (two equally-short paths around a box). Passable cells are 0, 2, or 3; walls are 5. Rule: find ALL SHORTEST PATHS from the red start to the green goal through passable cells (4-connectivity, walls 5 block). Compute the INTERSECTION — every cell that lies on EVERY shortest path. PAINT those cells with COLOR 8 (cyan). Red start and green goal stay. For single-corridor topologies the whole path becomes cyan; for rectangle-perimeter topology only the start/goal corners (intersection cells) get painted. Net: intersection of all shortest paths highlighted in cyan.

Kind: `per_puzzle`. Imported version: `2.0.2`.
Approval is derived by the catalog from current code and retained evidence.
