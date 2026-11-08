# 6d543ee31dda

0-bg grid containing 2 hollow color-6 FRAMES (placed at distinct columns, same row band) and 2 hollow color-7 FRAMES (placed at distinct rows, same column band). All 4 frames have IDENTICAL interior dimensions (ih × iw, ~4-6 each). Each frame's interior holds 3-6 non-bg cells in a single non-{0,6,7} color (the interior pattern). Frames don't overlap. Rule: sort 6-frames by column → COLUMN SHAPES (binary interior masks). Sort 7-frames by row → ROW SHAPES. For each (row-shape, col-shape) pair, compute cell-wise AND of their masks → paint with color 8. Build gallery: hstack horizontally for each row shape with 1-col gap, then vstack the rows with 1-row gap.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
