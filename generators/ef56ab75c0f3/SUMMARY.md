# ef56ab75c0f3

0-bg grid (h~7-9, w~9-11) with COLOR-4 (yellow) OUTER WALL BORDER. Interior holds: (a) ONE COLOR-2 (red) START cell and ONE COLOR-3 (green) GOAL cell at Manhattan distance ≥4; (b) optionally (use_k1=1) ONE COLOR-5 KEY1 and ONE COLOR-6 DOOR1; (c) optionally (use_k2=1) ONE COLOR-7 KEY2 and ONE COLOR-8 DOOR2; (d) 0-2 EXTRA INTERIOR WALL cells (color-4). Rule (BFS WITH 2-KEY MAZE): search shortest path from RED START to GREEN GOAL via 4-conn 0-cells. WALLS (4) block. DOORS (6, 8) block UNLESS the matching KEY (5 or 7) has been picked up earlier on the path. PAINT every cell on the shortest valid path with COLOR 9 (maroon). Net: 2-key maze shortest-path traced in color 9.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
