# 561ebfa521f0

Grid with color-5 BORDER (outer ring of walls). Interior is mostly 0-bg with a few scattered 5-walls forming obstacles. Three markers: color-2 (red), color-4 (yellow), color-3 (green) placed at distinct interior positions, all reachable from each other through non-wall cells. Rule: BFS shortest path 2→4 (union of all shortest paths). BFS 4→3. Paint cells on either leg's union with color 8 (only cells that are currently 0). Walls and markers preserved.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
