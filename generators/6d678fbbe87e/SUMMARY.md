# 6d678fbbe87e

0-bg grid (h, w ~5-7) with 1-2 PARTIAL 2×2 BLOCKS. Each block: 3 same-color cells + 1 zero cell at one corner, fitted in a 2×2 region. Blocks are in distinct colors and placed apart by ≥1 bg cell. Rule: scan every 2×2 window (r, c)..(r+1, c+1). If the 4 values contain exactly 3 cells of one non-zero color AND 1 zero cell → fill that zero cell with the block's color. All other cells preserved.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
