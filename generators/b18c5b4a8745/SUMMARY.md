# b18c5b4a8745

Grid (h~9-13, w~10-15) with: (a) color-5 (gray) WALLS forming a central vertical wall (with a gap) and horizontal cross-walls; (b) exactly ONE color-2 (red) seed on the left side and ONE color-3 (green) seed on the right side. Rule: do BFS-shortest-path distance from all red cells (d2) and from all green cells (d3), treating color-5 cells as impassable. For each cell: if input != 0 → keep it. Else compare d2 vs d3: if d2 < d3 → paint 2; if d3 < d2 → paint 3; tie → 0. Net: wall-aware nearest-seed Voronoi between red and green.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
