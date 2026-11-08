# 58b6f34fd9b2

15 × w grid (w ~3-14), composed of THREE stacked 5-row PANELS at rows 0-4, 5-9, 10-14. Each panel uses values from {0, 1, 6, 8} in some pattern (random/blob/stripes/checker/border/diagonal/scatter). Rule: output = 5 × w grid. For each (r, c) in output, look at the 3 stacked cells g[r][c], g[r+5][c], g[r+10][c]. Compute the cell by priority OR: if ANY of the 3 is 6 → output 6; else if ANY is 1 → output 1; else if ANY is 8 → output 8; else → 0. Net effect: 3-way overlay with color precedence 6 > 1 > 8 > 0.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
