# Solve work log

Earlier exposure: none. I did not open any generator, Racket rule, private labels,
reference solution, or prior task notes before this blind solve.

## Revision 1

The visible outputs preserve the canvas, every nonzero color, every column, and
the top-to-bottom order of colored cells within that column. The only change is
that each column's nonzero cells fall to the bottom, with zeros above them.

Checks on the examples:

- Example 0, column 2: `3` above `9` becomes rows 5 and 6 in the same order.
- Example 1, column 2: `9, 9, 6` becomes the bottom three cells.
- Example 3, columns 6 and 7: the irregular `8/7` cells compact independently,
  explaining why column 7 ends as `8, 7` at the bottom while column 6 ends as
  `8, 7` at the bottom.
- Example 4 confirms independent column behavior rather than treating all colors
  as one connected object.

Implemented column-wise downward gravity with zero as background. Remaining
uncertainty is limited to whether zeros are always background; all five visible
examples support that interpretation.
