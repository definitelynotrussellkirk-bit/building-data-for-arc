# Solve notes: 7e19bce9c44c

## Visible-example observations

All three outputs are rectangular subgrids copied verbatim from their inputs.
The removed cells are exactly complete outer rows and columns of zeroes.  The
remaining rectangle begins at the minimum row/column containing any nonzero
cell and ends at the maximum such row/column.

The first example is especially discriminative: its 4x4 output retains an
entire internal all-zero row, so the operation is not "delete every blank row"
or "pack the coloured cells."  Its three colours also contribute jointly to
the bounds, so the object is the union of all nonzero cells rather than one
connected component or one selected colour.

## Hypothesis

Return the tight axis-aligned bounding-box crop of every nonzero input cell,
preserving every value—including zero holes—inside that box.

## Implementation choice

Collect all nonzero coordinates, compute their row/column minima and maxima,
and slice the original grid inclusively.  The visible examples contain nonzero
content; an empty input is handled defensively by returning an empty grid.

## Exposure declaration

This is the required post-repair exposed solve.  I had already reviewed this
task's generator and intended rule before the episode, so earlier exposure is
`yes`.  During this solve episode I read only `solve/challenge.json` and did not
consult the Racket source, generator source, reference solutions, or masked
labels.
