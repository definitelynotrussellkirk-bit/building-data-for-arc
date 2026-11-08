# 76f83b6b4879

0-bg grid (h~9-13, w~11-16) with: (a) WALLED QUADRANT STRUCTURE — two FULL-HEIGHT (or near-full-height) COLOR-5 (gray) WALL COLUMNS at c1 = w//3 and c2 = (2*w)//3, with small gaps near row h//2 (passable openings); plus a horizontal stretch of color-5 wall cells along row h//2 (sparse, leaving gaps near the wall columns); (b) THREE COLORED SEEDS — color 2 (red) at (1, w//2) in the top region, color 4 (yellow) at (h-2, 2) bottom-left, color 3 (green) at (h-2, w-3) bottom-right. Rule (WALL-AWARE BFS FLOOD WITH TIES → CYAN): For EACH 0-cell, compute BFS DISTANCE through 0-cells (4-connected, blocked by 5-walls) to EACH of the 3 seeds. If one seed has STRICTLY LESS distance, PAINT the cell with that seed's color. If ≥2 seeds TIE for minimum distance, PAINT with COLOR 8 (cyan). Unreachable cells stay 0. Walls and seeds stay. Net: each empty cell goes to its nearest seed's color, ties become cyan.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
