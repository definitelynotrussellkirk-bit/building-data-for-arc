# Post-repair visible-example solve notes

This is a human-readable work log, not a hidden model trace. I had earlier rule
exposure from repairing the assigned generator, so this episode is intentionally
reported as exposed even though I did not reopen the generator, Racket source,
reference answers, or private labels during the solve.

## Initial hypothesis

Across all three visible examples, color 2 forms two 4-connected components:
one is a simple horizontal or vertical line and the other bends or branches.
Only the two extreme cells of the whole straight component change from 2 to 4.
The bent/branched red component is copied unchanged. Existing non-red colors,
including input color 4, are also copied unchanged.

The important object boundary is component-level rather than run-level: in the
first demonstration the branched T contains horizontal and vertical runs, but
none of their local endpoints change.

## Predicted queries

- Query 1: preserve the left T-shaped red component; change the top and bottom
  cells of the separate three-cell vertical line in column 6 to 4.
- Query 2: preserve the lower L-shaped red component; change the first and last
  cells of the separate five-cell vertical line in column 5 to 4.

## Implementation

Find 4-connected color-2 components. For each component, test whether all rows
or all columns agree. Recolor its extrema only in that case. No revision was
needed after the first visible-example check.
