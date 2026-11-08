# a3a85fedfec1

0-bg grid (h~8-10, w~9-11). ROW 0: 2-3 distinct non-zero PRIORITY colors at distinct columns (left-to-right order = rank, with leftmost = highest priority). ROWS 1+: 3-5 SEED CELLS in colors drawn from the priority palette, placed with Manhattan distance ≥ 2 from each other. Rule: extract priority = row 0 non-zero values in scan order. Seeds = body cells with non-zero value, shifted up by 1 row. Output grid = (h-1) × w. For each output cell (r, c), find the highest-priority seed whose Manhattan distance to (r, c) is ≤ 1 (i.e., a plus-radius-1 from the seed). Paint with that seed's color. If no seed covers it, 0. Net effect: each seed grows a + (plus shape), overlaps win by priority rank, output drops row 0.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
