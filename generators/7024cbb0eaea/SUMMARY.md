# 7024cbb0eaea

0-bg grid (h, w~7-10) with 1-2 SOLID 3×3 RINGS — each ring is a 3×3 block of cells where the 8 OUTER cells (top row, bottom row, left col, right col of the 3×3) are filled with a single non-bg COLOR, and the CENTER cell at (r+1, c+1) is 0 (empty). Each ring uses a distinct color, and rings are placed with at least 1-cell gap so they don't touch. Rule: for every cell whose all 8 neighbors are NON-ZERO and SAME-COLOR (a ring center), FILL that center cell with the ring's color. Net: each hollow 3×3 ring becomes a solid 3×3 square of its color.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
