# Solve work log

## Exposure declaration

I had already reviewed this task's generator and canonical rule before this
post-repair episode, so this is an **exposed** solve, not a blind capability
measurement. During the solve itself I used only the visible examples in
`solve/README.md`; I did not open the generator, Racket source, reference
solution, private labels, or previous solution explanations.

## Revision 1

**Observed transformation.** Input and output keep the same shape. Every changed
row contains one nonzero, non-gray colored cell to the left of a gray `8`. The
output copies that colored cell rightward across all intervening zeros and stops
immediately before the gray cell. Blank rows and cells after the gray cell stay
unchanged. Examples include both long spans and a one-cell span, so the operation
is row-local rather than a fixed-length extension.

**Hypothesis.** In each row, find the first color other than `0` or `8`; find the
first `8` to its right; fill the open interval between them with the emitter's
color. If either endpoint is missing, leave that row unchanged.

**Program.** Deep-copy the grid, apply the row rule independently, and return the
copy. This preserves input immutability and any material outside the interval.

**Alternatives considered.** Extending to the row edge is contradicted by every
visible blocker. Filling leftward or both directions is contradicted by unchanged
zeros before the emitter. Using a global color or fixed number of cells is
contradicted by rows with different colors and span lengths.

**Remaining uncertainty.** The examples do not exhaust malformed rows with
multiple possible emitters or blockers. The implementation follows the most
literal visible convention: first emitter, then first gray blocker to its right.
