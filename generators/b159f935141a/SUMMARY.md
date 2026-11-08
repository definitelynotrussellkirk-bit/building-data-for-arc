# b159f935141a

0-bg grid (h~5-7, w~7-9) with 2-3 PLUS-PATTERNS at scattered interior positions. Each plus-pattern is 4 cells of a SINGLE non-zero color arranged at the 4 CARDINAL NEIGHBORS of a center position (r, c): cells at (r-1, c), (r+1, c), (r, c-1), (r, c+1). The CENTER cell at (r, c) is initially 0. Plus-patterns use DISTINCT colors and are 2-cell spaced apart so they don't overlap. Rule: for EVERY 0-cell at (r, c) whose 4 CARDINAL NEIGHBORS are ALL the SAME non-bg color v, RECOLOR that 0-cell to COLOR v. Net: each plus-pattern's empty center gets filled with the surrounding color, completing the plus into a 5-cell monochrome plus shape.

Kind: `per_puzzle`. Imported version: `2.0.2`.
Approval is derived by the catalog from current code and retained evidence.
