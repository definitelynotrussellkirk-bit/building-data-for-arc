# 903a3800b1b3

Grid (h×w, h=3..15, w=6..15) with bg color ∉ {4, 6} and scattered color-4 (yellow) cells in various layouts (random, cluster, column, row, diagonal, scattered). Optional decor cells in other colors. At least one yellow cell sits at a column where col % 3 == 0. Rule: for each cell, if color == 4 AND column index % 3 == 0, recolor to 6 (magenta). Otherwise keep original. Output: yellows in trigger columns become magenta; yellows elsewhere stay 4.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
