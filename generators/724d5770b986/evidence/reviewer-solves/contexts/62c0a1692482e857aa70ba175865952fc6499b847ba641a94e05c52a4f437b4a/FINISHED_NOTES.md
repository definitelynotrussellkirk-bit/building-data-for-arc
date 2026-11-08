# Solve work log

Earlier exposure before this blind solve: none known. I did not open this task's generator, canonical rule, reference solution, private labels, or prior notes.

## Observation and hypothesis

Across all three visible examples, the only changed cells are background zeros changed to color 1. Each original color-1 cell acts as a seed. The changed cells are exactly the zero-valued cells in the seed's clipped 3×3 Moore neighborhood (row offset -1..1 and column offset -1..1). Existing nonzero cells, including other colors, are preserved. Newly painted 1s do not recursively seed further growth; neighborhoods are computed from the original input.

## Probe

I enumerated original 1 positions and all input/output differences from `challenge.json`. For every seed, the union of zero cells in its 3×3 neighborhood matched the observed differences, including edge clipping and overlapping neighborhoods. A pre-implementation visible-example test failed with the expected `NotImplementedError`, confirming the test exercised the placeholder.

## Implementation

`solve(grid)` copies the input, snapshots all original color-1 positions, and paints only original zero cells inside each clipped 3×3 neighborhood. Remaining uncertainty is limited to whether a hidden case contains no 1s; under the inferred rule such a grid is returned unchanged.
