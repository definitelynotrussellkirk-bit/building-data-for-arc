# Visible-only solve log

## Observation

All four outputs are exact rectangular slices of their inputs. The slice starts
at the smallest row and column occupied by any nonzero cell and ends at the
largest occupied row and column. Interior zeros, gaps between disconnected
objects, and every original color are retained.

Examples 1 and 3 are decisive against cropping one component: their nonzero
cells are disconnected and differently colored, yet one joint bounding box is
returned. Examples 0 and 2 show that the crop does not fill holes or recolor.

## Hypothesis

Return the tight bounding rectangle containing **all** nonzero cells. For an
all-zero input, return `[[0]]` as a total-function fallback; that case is not
shown and does not affect the visible queries.

## Predicted queries

- Query 0: rows 2..3 and columns 2..3, preserving the orientation
  `[[7, 7], [0, 7]]`.
- Query 1: rows 4..6 and columns 2..5, preserving both colors and the blank
  middle row.

## Implementation

`solution.py` finds all nonzero coordinates, computes their min/max row and
column, and returns that inclusive subgrid. No generator, Racket rule, private
label, or reference solution was consulted during this solve phase. I had seen
the task rule earlier while repairing the assigned generator, so this is an
exposed post-repair solve, not a blind solve.
