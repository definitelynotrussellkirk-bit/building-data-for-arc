# Solve notes

This is a human-readable work log based only on `solve/challenge.json` during the solve phase. It is not a token-level model trace. I had seen the task rule earlier while reviewing the generator, so this is not blind; I did not reopen the generator, Racket source, reference solution, or private labels during this phase.

## Visible structure

Every visible grid is 11×11. Rows 3 and 7 and columns 3 and 7 are all zero, dividing the nonzero cells into nine 3×3 blocks. The outputs retain the same separators and reuse whole 3×3 textures, suggesting permutation rather than repainting.

I counted color-1 cells in row-major macro-block order:

- Train 0 input: `[9, 4, 2, 6, 5, 0, 3, 7, 8]`; output: `[7, 8, 9, 4, 5, 6, 0, 2, 3]`.
- Train 1 input: `[3, 8, 2, 0, 6, 4, 5, 7, 1]`; output: `[6, 7, 8, 3, 4, 5, 0, 1, 2]`.
- Train 2 input: `[8, 2, 0, 3, 6, 5, 9, 4, 7]`; output: `[7, 8, 9, 4, 5, 6, 0, 2, 3]`.

The outputs therefore globally rank blocks by number of 1s. Ascending rank is placed left-to-right beginning on the **bottom** macro-row, then the middle row, then the top row. Equivalently, each row is ascending left-to-right while rows contain high, medium, then low thirds from top to bottom.

## Rejected alternatives

- Sort ascending in ordinary top-left row-major order: contradicted by all three output count sequences.
- Sort only within each existing macro-row: contradicted because blocks cross row boundaries.
- Repaint standardized shapes from counts: contradicted because the output preserves each input block's exact internal arrangement.
- Sort by number of 2s: this reverses the rank and does not match the left-to-right order inside rows.

## Revision 1

Extract the nine 3×3 blocks, attach each block's count of 1s, sort ascending, and place sorted blocks at bottom-left through bottom-right, then middle-left through middle-right, then top-left through top-right. Initialize an all-zero 11×11 result so separators remain zero.
