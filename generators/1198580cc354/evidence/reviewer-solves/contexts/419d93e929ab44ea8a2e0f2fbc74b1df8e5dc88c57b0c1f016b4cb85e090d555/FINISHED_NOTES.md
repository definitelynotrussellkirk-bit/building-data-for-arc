# Solve work log

## Prior exposure

I had not opened this task's generator, canonical rule, reference solution, notes,
or private labels before solving. I used only the visible examples produced by
`python3 review.py blind prepare`.

## Revision 1 — vertical rays stopped by maroon blockers

Across all three training examples, every non-black cell in the first row acts
as the source of a vertical line of the same color. The line fills black cells
below it through the last row unless a maroon (`9`) cell occurs in that column.
A maroon cell is preserved and stops the line; cells below it remain black.
Columns without a colored source in the first row are unchanged.

This explains the differing line lengths in examples 0–2 and all unchanged
maroon cells. I implemented the rule by copying the grid, scanning each first-row
source color except `0` and `9`, and filling downward until the first `9`.

Remaining uncertainty: the visible examples contain no non-maroon obstruction
below a source. The implementation conservatively preserves any such nonzero
cell while continuing the ray, because only `9` is demonstrated as a blocker.
