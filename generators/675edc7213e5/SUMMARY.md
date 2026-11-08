# 675edc7213e5

0-bg grid (h, w~8-13) with multiple color-2 (red) RECTANGULAR BLOCKS placed at varying positions. Layout: 2×2 RED CORNER block at (0, 0) [top-left] touches top + left borders (2 borders); 2×2 RED CORNER block at (h-2, w-2) [bottom-right] touches bottom + right (2 borders); 2×1 RED block on top edge at a random column (touches top border only → 1 border); 2×2 RED block at (h//2, w//2) [center] touches 0 borders. Components are 4-conn isolated. Rule: count how many of the 4 GRID BORDERS each color-2 component touches (a border is touched if any cell of the component lies on row 0, row h-1, col 0, or col w-1). For every component touching EXACTLY 2 borders, RECOLOR all its cells from 2 to 3 (green). Components touching 0, 1, 3, or 4 borders stay red. Net: only the corner blobs (touching exactly two borders) turn green.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
