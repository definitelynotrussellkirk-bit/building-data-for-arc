# Solve work log

## Prior exposure

This is an exposed post-repair solve. Before preparation I had already reviewed the assigned generator and canonical rule, so `earlier-exposure` must be recorded as `yes`. During this solve lane I used only the visible examples printed by preparation and did not reopen the generator, Racket source, reference answers, private labels, or earlier solution explanations.

## Revision 1

Visible pattern: each input contains exactly one same-colored full row and full column, forming a cross, plus one to three gray (`5`) marker cells. The output removes all gray cells and redraws the same-colored cross. Across the three demonstrations, if `N` is the number of gray cells, the cross center moves from `(row, column)` to `(row + N, column - N)`:

- example 0: one gray, `(4,5) -> (5,4)`;
- example 1: two grays, `(0,2) -> (2,0)`;
- example 2: three grays, `(9,13) -> (12,10)`.

I implemented that literal count-based rule. The solver identifies the unique complete nonzero/non-gray row and column rather than relying on connected components or marker geometry, counts all gray cells, checks the shifted center remains in bounds, and paints only the shifted cross. A plausible wrong alternative would use the number of gray-bearing rows or their span, but the second visible example has two grays on one row, so those alternatives would move by one and contradict its output.

Remaining uncertainty is limited to the masked queries; the visible examples determine the direction, distance, color preservation, shape preservation, and marker erasure consistently.
