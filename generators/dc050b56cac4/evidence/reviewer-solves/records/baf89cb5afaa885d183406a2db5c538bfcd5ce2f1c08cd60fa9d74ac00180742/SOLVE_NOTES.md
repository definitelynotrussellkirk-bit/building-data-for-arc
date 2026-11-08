# Solve notes

This is the required post-repair solve. I had already seen the generator/rule during repair work, so this is not blind; I did not consult the generator, Racket source, private labels, or prior solution text during this solve.

From the visible examples:

- Each input has one solid nonzero/non-gray row and one solid column of the same color. Their intersection is the cross center.
- The gray cells are removed from the output.
- Let `N` be the total number of gray (`5`) cells. The output cross center moves `N` rows down and `N` columns left.
- The output keeps the input dimensions and cross color; all other cells become black.

Checks from the three demonstrations:

- Example 0: center `(4,5)`, one gray -> `(5,4)`.
- Example 1: center `(11,14)`, two grays -> `(13,12)`.
- Example 2: center `(9,3)`, three grays -> `(12,0)`.

Implementation therefore finds the unique solid row/column, counts all gray cells, and redraws the shifted cross on a zero grid.
