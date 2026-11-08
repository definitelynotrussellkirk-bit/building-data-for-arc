# a9889198baf3

0-bg grid (h, w~7-10) with 2-5 SINGLETON SEEDS — single non-0 cells placed at positions on a 3-cell stride grid (rows 0, 3, 6, ...; cols 0, 3, 6, ...) so their 2×2 expansions don't conflict. Each seed uses a DISTINCT color from {1..8} (color (i % 8) + 1). Rule (EXPAND EACH SINGLETON INTO A 2×2 SAME-COLOR BLOCK, ANCHORED AT THE SEED AS TOP-LEFT): For EACH SINGLETON SEED at (r, c) with color C: PAINT the cells (r, c), (r, c+1), (r+1, c), (r+1, c+1) with color C. The seed stays. Net: every non-0 cell becomes the top-left corner of a 2×2 solid block in its color.

Kind: `per_puzzle`. Imported version: `2.0.2`.
Approval is derived by the catalog from current code and retained evidence.
