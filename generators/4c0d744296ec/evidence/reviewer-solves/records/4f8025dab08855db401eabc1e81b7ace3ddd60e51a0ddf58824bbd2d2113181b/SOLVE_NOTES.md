# Solve work log

## Prior exposure

This is the required post-repair exposed solve. Before preparation I had already
read and repaired the task generator and had seen the intended transformation,
so `earlier-exposure` must be recorded as `yes`. During this solve episode I did
not reopen the generator, Racket rule, canonical answers, prior solution
explanations, or private query labels. The implementation below was checked only
against the visible examples printed by `prepare`.

## Revision 1

All three visible examples preserve the input dimensions. Their only nonzero
cells are in the first row. In each output, that entire first-row pattern is
repeated unchanged for every output row: marked columns become vertical stripes
of their original colors, while zero columns stay zero. This holds for heights
7, 8, and 10; widths 8 and 9; and two, three, or six colored markers.

Hypothesis: return `len(grid)` independent copies of `grid[0]`. Copy each row
rather than aliasing the same list. The two visible queries have the same input
structure, so no exception is indicated. Remaining uncertainty is only the
withheld query scoring; there is no unresolved visible-example mismatch.
