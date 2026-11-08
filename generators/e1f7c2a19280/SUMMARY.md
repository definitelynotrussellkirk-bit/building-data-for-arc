# e1f7c2a19280

Maze grid (h×w, ~8-13 by ~9-15) with color-5 (gray) BORDER walls around the entire perimeter and 0 interior. EXACTLY ONE color-2 (red) marker and ONE color-3 (green) marker placed in the interior at distinct positions. Optionally, 5-8 INTERIOR wall cells (color 5) scattered in the interior, creating asymmetric path obstacles (not blocking either marker from anything else). Rule: BFS from red and from green through 0-cells, avoiding 5-walls (4-conn). For each 0-cell reachable from BOTH markers, if dist_red == dist_green, paint it color 8. Output: markers + walls preserved, plus a 'perpendicular bisector' of color 8 cells.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
