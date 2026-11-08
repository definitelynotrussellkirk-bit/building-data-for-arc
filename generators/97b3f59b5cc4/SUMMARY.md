# 97b3f59b5cc4

0-bg grid (h×w, ~5-8 by ~7-10) with 3-5 connected non-zero components in distinct colors. At least 2 components TOUCH the grid BORDER (any cell on row 0, row h-1, col 0, or col w-1). At least 2 components are entirely INTERIOR (no cell on the border). Components are 8-conn isolated (≥1-cell buffer). Rule: for each connected component, check if any cell sits on the grid border. If yes, KEEP it with original color. If no, ERASE it (cells become 0). Output: only border-touching components survive.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
