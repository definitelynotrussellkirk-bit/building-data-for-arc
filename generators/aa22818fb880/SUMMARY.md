# aa22818fb880

0-bg grid (h~8-11, w~8-11) with 2-4 isolated PARTIAL PLUS motifs. Each plus: a center cell + 3 same-color cardinal arm cells (up, down, left, right minus one). The missing 4th arm cell is bg (0), in-bounds, and the remaining 3 arms are all the same color. Different pluses use distinct colors; motifs isolated by ≥2 bg cells on all sides. Rule: scan every cell. For each non-bg cell, count how many of its 4 cardinal neighbors have the same color. If exactly 3 → identify the missing cardinal direction and paint that neighbor with the cell's color (if in bounds and currently 0). Net effect: complete each partial plus by filling its missing arm.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
