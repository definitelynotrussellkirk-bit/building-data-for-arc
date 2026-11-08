# Solve work log

## Exposure declaration

Before this blind episode I had read only the packet-level instructions and the visible presentation produced by `solve_episode.py blind prepare`. I did not open this task's generator, canonical rule, reference solution, private labels, notes, or audit records.

## Revision 1 hypothesis

For every nonzero color, the input contains two 4-connected components:

1. one isolated cell, which is a destination marker; and
2. one larger polyomino elsewhere in the grid.

The output erases the original components and translates the larger polyomino without rotation or reflection so that the top-left corner of its bounding box coincides with the isolated marker. The marker itself therefore becomes the polyomino's top-left occupied cell.

Evidence from the visible examples:

- Train 0 moves the color-7 T tetromino from rows 8–9 to marker `(3,5)`, preserving offsets `(0,0),(0,1),(0,2),(1,1)`.
- The color-4 five-cell T shape similarly moves from bounding-box corner `(10,11)` to marker `(2,11)`.
- Train 2 confirms the same rule for a horizontal bar and for two different zigzag/L shapes; no rotation is performed.

I implemented color-wise 4-connected component extraction, selected the unique singleton and unique larger component, translated the larger component by its bounding-box minimum, and rebuilt the output on a zero background. A conservative fallback preserves unmatched components if a color does not have the visible one-marker/one-shape structure.

## Local probe

Before implementation, a visible-example harness failed at the template `NotImplementedError`, confirming the harness exercised the solution. After implementation I planned to run the same harness and the official visible-only checker. No private query labels were inspected.

## Remaining uncertainty

The visible examples do not show multiple non-singleton components of one color or a marker that is not the top-left occupied point of the moved shape. The one-marker/one-shape interpretation is nevertheless consistent across every visible color and shape.
