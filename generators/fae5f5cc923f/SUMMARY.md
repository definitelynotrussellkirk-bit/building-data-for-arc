# fae5f5cc923f

0-bg grid (h, w ∈ 6-14, by difficulty) with: N_BLOCKS ∈ 1-4 SOLID 2×2 COLOR-5 (GRAY) BLOCKS, each placed at non-overlapping interior positions with ≥BLOCK_SEPARATION (default 5) cells between block top-lefts, ensuring ≥2-cell buffer from all grid edges. Position biases ∈ {scattered, diagonal, row_aligned, centered}. Rule (FOR EACH 0-CELL (R, C), CHECK THE 4 DIAGONAL 2×2-RELATIONS TO 5-BLOCKS: IF A 2×2 5-BLOCK SITS AT (R+1..R+2, C+1..C+2) (BOTTOM-RIGHT DIAG): PAINT (R,C) = COLOR 1; IF AT (R+1..R+2, C-2..C-1) (BOTTOM-LEFT): COLOR 2; IF AT (R-2..R-1, C+1..C+2) (TOP-RIGHT): COLOR 3; IF AT (R-2..R-1, C-2..C-1) (TOP-LEFT): COLOR 4; PICK THE FIRST MATCHING IN BR/BL/TR/TL ORDER): For EACH 0-cell, check the 4 diagonal relations to gray 2×2 blocks. PAINT with the first-matching corner marker (1, 2, 3, or 4). Blocks preserved. Net: each 2×2 block gains 4 distinct-colored corner markers at its diagonal 2-cell offsets.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
