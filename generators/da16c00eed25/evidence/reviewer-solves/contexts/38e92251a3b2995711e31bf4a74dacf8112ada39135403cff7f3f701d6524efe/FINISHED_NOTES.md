# Solve notes

This is a human-authored work log based on `solve/challenge.json`. I had already
seen the task rule while reviewing the generator, so this is not a blind solve;
I did not consult the generator, Racket source, reference solutions, or masked
query labels after episode preparation.

## Visible-example observations

Each training input has exactly three equal nonzero cells. Their coordinates use
exactly two row indices and two column indices, so they occupy three products of
a 2×2 row/column Cartesian product. The output preserves every cell and paints
the sole absent product with the same color.

The examples deliberately cover:

- adjacent rows/columns at the top-left boundary;
- a separated lower-right missing corner;
- a separated lower-left missing corner;
- a top-right missing corner touching the left boundary.

This rules out "always fill the lower row", "require a blank gap", and "ignore
edge-touching shapes". The two test inputs have the same three-corner invariant.

## Implementation

Collect the three nonzero cells, require one shared color and exactly two rows and
two columns, find the unique row-column pair not already occupied, copy the grid,
and paint that pair. Validation is included so malformed inputs fail explicitly
rather than producing an arbitrary edit.
