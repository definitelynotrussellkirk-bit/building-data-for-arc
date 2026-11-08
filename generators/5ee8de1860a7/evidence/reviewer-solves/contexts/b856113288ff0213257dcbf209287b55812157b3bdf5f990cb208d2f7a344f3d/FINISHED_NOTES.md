# Solve notes

## Visible evidence

All three demonstrations contain a single nonzero interior cell. The output
keeps the same dimensions, removes that interior marker, and paints every cell
of the outer border with the marker's color. The marker location changes across
examples and is therefore not copied geometrically; only its color is used.

## Hypothesis

Find the sole nonzero color, create a same-sized zero grid, and paint its first
and last rows plus first and last columns with that color.

## Implementation check

The implementation does not assume a fixed shape, fixed color, or centered
marker. It preserves the input dimensions and uses only the unique nonzero
value. No alternate hypothesis was needed from the visible examples.
