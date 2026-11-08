# 99da65b07d44

Small 0-bg grid (h, w~2-4) with 2-4 SINGLE-CELL MARKERS at distinct positions in random non-zero colors from {1..9}. Other cells are bg. Rule: UPSCALE the grid by FACTOR 2 — every cell at (r, c) with value v becomes a 2×2 BLOCK of color v at output positions (2r, 2c), (2r, 2c+1), (2r+1, 2c), (2r+1, 2c+1). Output dimensions: 2h × 2w. Net: input is a small markered grid; output is the same pattern but each cell expanded to a 2×2 block (2× upscale).

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
