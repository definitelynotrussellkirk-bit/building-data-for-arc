# Solve work log

I had not seen this task's generator, Racket rule, reference solution, private labels,
or earlier solution explanation before solving. I used only the visible challenge.

## Revision 1 — baseline diagnostic

I first ran the untouched `NotImplementedError` stub as a diagnostic probe. It
errored on all three visible examples, confirming the checker was exercising the
submitted function rather than accepting a stale result.

## Revision 2 — partition rule

Across all three visible examples, color 3 forms complete horizontal and vertical
separator lines. These lines partition the canvas into rectangular bands. The
output preserves every separator cell and recolors whole non-separator regions by
position:

- upper-left corner region → 2
- upper-right corner region → 4
- lower-left corner region → 1
- lower-right corner region → 8
- regions bounded by separators on all four sides → 7
- non-corner regions on the outer border → 0

The implementation detects full-3 separator rows and columns, assigns each other
cell a row-band and column-band index by counting preceding separators, and applies
that positional coloring. This handles unequal band sizes and any number of
separator lines. Remaining uncertainty is limited to unseen malformed inputs with
no complete separator rows or columns; the visible task consistently uses this
partition grammar.
