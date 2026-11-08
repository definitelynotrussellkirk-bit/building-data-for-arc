# de4b26ce5373

0-bg grid (h~7-9, w~8-11) with: (a) 1-2 color-2 (red) EMITTER cells at interior positions; (b) 1-2 short straight color-8 (cyan) WALL SEGMENTS — horizontal or vertical lines of length 3-5 cells. Walls and emitters are placed so they are NOT 4-adjacent. Rule: for each color-2 emitter at (r, c), CAST FOUR RAYS in the cardinal directions (up, down, left, right). Each ray walks one cell at a time, painting that cell color 2 (red), until it either steps onto a color-8 wall cell (stop and do NOT paint the wall) or steps out of the grid. Walls stay 8; emitters stay 2. Net: each red dot emits red rays in all four directions that terminate at cyan walls or the grid border.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
