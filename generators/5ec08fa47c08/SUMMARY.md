# 5ec08fa47c08

Small 0-bg grid (h~5-7, w~5-7) with 2-4 distinct NON-BG COLORS scattered at isolated single-cell positions, each color appearing 1-2 times. Rule: list the distinct non-bg colors in the grid (in the order grid-colors returns them — typically by first appearance / numeric order). For EACH such color k with count count_k, EMIT count_k consecutive rows of color k stacked on top of each other. Output is a SINGLE-COLUMN GRID whose total height equals the total non-bg cell count, partitioned into per-color blocks. Net: input is a sparse multicolor scatter; output is a tall single-column color tally — one cell per non-bg input cell, grouped into solid color bands.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
