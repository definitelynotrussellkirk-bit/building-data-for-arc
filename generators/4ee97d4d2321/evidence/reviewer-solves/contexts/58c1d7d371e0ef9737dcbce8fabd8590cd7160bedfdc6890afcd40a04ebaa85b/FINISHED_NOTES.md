# Solve work log

## Exposure declaration before solving

I had already inspected this task's generator and canonical rule while performing the assigned repair, so this is an exposed post-repair solve, not a blind solve. During this solve phase I consulted only `solve/challenge.json`; I did not reopen the generator, Racket source, reference solutions, or private labels.

## Revision 1 — vertical-axis reflection

Visible examples all contain one full-height column of color 8. Nonzero cells outside that column remain in place and are copied to the same row at equal horizontal distance on the opposite side. Copies whose reflected column would be outside the grid are omitted; the original cells remain. The transformation uses the original input as the source so newly written cells are not reflected a second time.

Alternative hypotheses rejected from the visible pairs: moving rather than copying objects (originals clearly remain), reflecting only one side (examples contain sources on both sides), and reflecting around the geometric center (the color-8 axis can be off-center).

Implementation: locate the all-8 column, deep-copy the grid, then write each nonzero non-axis cell to `2*axis-col` when that column is in bounds.
