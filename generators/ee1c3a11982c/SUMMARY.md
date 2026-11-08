# ee1c3a11982c

0-bg grid (h, w ~5-12) with 2-5 SPARSE non-bg SEEDS in distinct colors at random positions NOT in the last row or last column. Rule: for each non-bg seed at (r, c) with color k: PAINT every cell in row r from c to col w-1 (extending rightward to the last column) with color k. Then for the cell (r, w-1) — also paint every cell in col w-1 from r to row h-1 (extending downward to the last row) with color k. Net: each seed traces an L-shaped path right to the right edge, then down to the bottom-right corner.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
