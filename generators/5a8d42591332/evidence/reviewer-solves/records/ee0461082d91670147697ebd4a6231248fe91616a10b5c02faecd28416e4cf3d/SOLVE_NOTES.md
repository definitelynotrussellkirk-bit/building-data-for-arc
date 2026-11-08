# Solve work log

Before this solve I had not opened this task's generator, Racket rule, reference solutions, private labels, audit material, or prior solve records.

## Revision 1

The 11×11 grid is a comparison table.  Three 2×2 patterns of color 1 form the column keys across the top, and three 2×2 patterns of color 2 form the row keys down the left.  Blank separator rows and columns divide the keys and the nine 2×2 result cells.

For every result cell, compare the number of colored pixels in its row key with the number in its column key:

- row count greater than column count → fill the 2×2 cell with color 3;
- row count smaller than column count → fill it with color 4;
- equal counts → fill it with color 8.

This explains every result cell in all three demonstrations.  In particular, the third demonstration supplies counts 1, 4, 2 down the left and 3, 1, 3 across the top, yielding rows `[4,8,4]`, `[3,3,3]`, and `[4,3,4]`.

The implementation locates the first all-zero separator row and column, derives the block size and block starts, counts nonzero pixels in each key, and fills each result block.  Remaining uncertainty is whether a hidden episode could contain an earlier all-zero row or column inside a key, but the visible construction consistently uses the first full blank line as the separator.
