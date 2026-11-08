# Solve work log

## Exposure declaration before solving

I had already inspected the assigned generator and canonical rule during the required repair phase, so this is an exposed post-repair solve, not a blind solve. During this solve episode I did not reopen or consult the generator, Racket source, canonical examples, reference solutions, or private query labels; I used only `solve/challenge.json`.

## Revision 1 — independent column gravity

Across all five visible demonstrations, nonzero cells keep their original column and color. Within each column, their top-to-bottom sequence is preserved, while all empty vertical gaps are removed and the sequence is placed flush against the bottom row. Columns act independently: a six-cell stack in one column moves only enough to touch the floor, while singleton or shorter columns fall farther.

Implementation: collect nonzero values from each column in row order, create an all-zero output of identical dimensions, and write that sequence into the bottommost rows of the same column. This also handles repeated colors and columns already touching the bottom without treating bottom contact as a freeze condition.

No competing visible hypothesis survived all examples: global row gravity would move cells horizontally, sorting colors would change order, and freezing a column that already touches the floor is contradicted by gapped supported columns.
