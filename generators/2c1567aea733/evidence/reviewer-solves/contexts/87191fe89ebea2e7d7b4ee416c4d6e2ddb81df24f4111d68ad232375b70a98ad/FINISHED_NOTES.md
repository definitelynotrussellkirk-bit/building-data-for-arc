# Solve work log

## Exposure declaration

Before this visible-only episode I had already inspected the assigned generator,
canonical task, and authority while repairing it, so earlier rule exposure is
**yes**. During this solve episode I consulted only `solve/README.md`, the visible
challenge grids printed by `prepare`, my own code, and visible-example feedback.
I did not reopen generator source, Racket source, reference solutions, private
labels, or earlier solution explanations.

## Revision 1

Hypothesis from the three visible demonstrations: color 1 is the anchor. For each
nonzero color, find its topmost occupied row and shift every cell of that color
vertically until that top equals color 1's original top. Keep columns unchanged
and preserve the full per-color shape, including disconnected cells.

Evidence:

- Example 0 moves colors 2 and 4 upward to blue's row 0 while blue remains fixed.
- Example 1 moves color 4 down and color 2 up to blue's row 1.
- Example 2 moves both other colors down to blue's row 2; the irregular blue and
  color-2 shapes keep their exact offsets.

I rejected identity, fixed highest/lowest/median-row alignment, component-wise
motion, and bottom-edge alignment because the examples require opposite shift
directions and preserve each color as one complete set of cells.

Implementation builds a blank same-sized grid, groups all nonzero cells by color,
computes the blue top, applies one row offset per color, and rejects clipping or
collisions. No failed natural revision preceded this implementation.
