# 1f3d51c86f9f

0-bg grid with: (a) several color-9 walls (often a vertical line or scattered); (b) several pairs of cells in distinct non-9 colors (each color appears at EXACTLY 2 cells). Rule: for each non-9 color with exactly 2 cells, draw an L-shaped path between them: try horizontal-then-vertical via the bend at (r1, c2); if any interior cell of that path is non-zero and non-same-color, fall back to vertical-then-horizontal via (r2, c1). Paint the path with the color, preserving the endpoints. Color-9 walls and 0-cells along the path are overwritten.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
