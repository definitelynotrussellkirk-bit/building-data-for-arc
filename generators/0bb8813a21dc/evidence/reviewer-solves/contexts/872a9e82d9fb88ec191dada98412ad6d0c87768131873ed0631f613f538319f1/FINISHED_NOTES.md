# Solve work log

## Exposure declaration

Before this solve I had already inspected the task's generator and canonical
rule while repairing the generator, so earlier rule exposure is **yes**. For
this source-bound solve I did not reopen the generator, the Racket rule,
reference solutions, private labels, or earlier solve notes. I used only the
fresh `solve/challenge.json` visible examples.

## Revision 1

Observed in every training row: zero positions remain zero, while all nonzero
positions keep their locations but take the color of the leftmost nonzero cell
in that row. Rows containing only zeroes are unchanged. This explains rows
with one color already present as well as mixed-color rows and rows with gaps.

Implemented `solve(grid)` row by row:

1. find the first nonzero value;
2. if none exists, copy the row;
3. otherwise replace each nonzero with that first value and preserve zeroes.

Alternative hypotheses rejected from the visible examples include using the
modal or rarest color, filling gaps, using the rightmost color, or applying one
global color across rows. The implementation has no shape or palette constants
and supports rectangular integer grids. Remaining uncertainty before the check
is only hidden-query correctness; the visible transformation is unambiguous.
