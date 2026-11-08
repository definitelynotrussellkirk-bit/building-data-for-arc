# 405c8d5c7709

12×12 grid filled with a single non-{0,2,4} BACKGROUND color, with 1-3 small CLUSTERS of color-2 (red) cells. Each cluster: 2-3 red cells placed within Chebyshev distance ≤ 2 of one another (so they merge into a single group). Different clusters are placed apart. Rule: (1) find the most frequent non-zero value bg in the grid. (2) collect all color-2 cells. (3) cluster them greedily by Chebyshev distance ≤ 2 (cells within radius-2 in any direction merge into the same group). (4) For each group, compute the bbox over its red cells. (5) Inside each bbox, set every bg cell (NOT red, NOT 4, NOT other) to color 4. Red cells inside the bbox stay red.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
