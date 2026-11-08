# Solve work log

## Exposure declaration

I had already read and repaired this task's generator and canonical rule before
this required solve, so this is **not blind**. During the solve phase itself I
used only the prepared visible examples and did not reopen the generator,
Racket source, reference solutions, or private labels.

## Visible-example observations

- Every input has background color `7` plus one complete non-7 row and one
  complete non-7 column. Their intersection defines horizontal and vertical
  reflection axes.
- Every colored/non-7 cell away from both axes appears at the other members of
  its fourfold orbit: mirror left/right, mirror up/down, and mirror across both.
- Cells on either axis stay part of the cross but do not act as sources. This is
  important in train example 1, whose cross contains off-color `5` cells.
- Reflections are clipped one target at a time. A source near an edge can still
  paint whichever reflected positions remain in bounds.
- Train example 1 contains sources in several quadrants and collisions. Reading
  the **original input** in row-major order explains the output: later sources
  overwrite earlier reflections, including an earlier source location. For
  example, the `5` at `(1,5)` paints `(3,5)`, then the original `0` at `(3,5)`
  later paints `(1,5)`.

## Hypotheses considered

1. **Reflect only sources from one populated quadrant.** Rejected by train
   example 1, where off-axis sources in multiple quadrants all affect the
   result.
2. **Treat every non-7 cell, including axis anomalies, as a source.** Rejected
   because the cross remains a separator and its off-color cells do not create
   extra copies.
3. **Fill each orbit simultaneously without overwrite order.** Rejected by the
   conflicting same-orbit values in train example 1. Row-major source order
   reproduces the visible overwrite pattern.
4. **Drop an entire source when one reflection is out of bounds.** Rejected by
   the edge-clipped sources in train example 1; valid counterparts are still
   painted.

## Implementation

Find the first all-non-7 row and column. Copy the grid, then scan the original
input row-major. For each non-7 off-axis cell, compute the three reflected
coordinates and paint each one that lies in bounds. The source scan never reads
from the evolving output, which prevents newly painted cells from becoming new
sources.

Remaining uncertainty is low because the three demonstrations jointly exercise
ordinary fourfold copying, multi-quadrant collisions/overwrite order, axis-cell
exclusion, and cellwise clipping.
