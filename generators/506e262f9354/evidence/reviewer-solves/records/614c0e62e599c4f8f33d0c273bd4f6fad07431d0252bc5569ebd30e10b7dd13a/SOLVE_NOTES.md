# Solve work log

## Exposure declaration

I had already inspected the selected rule while repairing this generator, so
this is an exposed solve (`earlier-exposure=yes`).  During this solve episode I
used only the visible examples in `solve/README.md`; I did not reopen the rule,
generator, reference solutions, or private labels.

## Hypothesis

The vertical run of color 7 supplies one source column and its bottom row.  For
an output row `r` at or above that bottom row, the horizontal reach is
`bottom_row - r`.  Fill every in-bounds cell at distance at most that reach;
use 7 at even distance from the source column and 8 at odd distance.  Everything
else is overwritten with 0, including the visible colors 3 and 6 outside the
triangle.

This explains the shifted source in examples 1 and 2: the triangle continues
above the first input 7, so its height is tied to the absolute bottom-row
coordinate rather than merely the number of source cells.  Edge columns simply
clip the triangle to the canvas.

## Revision 1

Implemented the hypothesis directly in `solution.py`: locate all 7s, validate a
single source column, take the maximum row, and render a fresh zero canvas with
the alternating horizontal-distance pattern.  No alternative implementation or
failed solve revision was needed.
