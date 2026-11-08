# Blind solve notes

## Observations

- Color 0 is background and color 6 is stationary in every visible example.
- For each non-6 colored cell, writing its offset from the 6 marker as
  `(dr, dc)`, the output offset is `(dc, -dr)`: a 90-degree clockwise rotation.
- The second training example demonstrates clipping: one rotated cell would land
  just beyond the right edge and is absent from the output.
- The third and fourth examples show that all non-background colors rotate by
  the same rule, preserving each cell's color.
- The fifth example contains two 6 cells.  Its output retains and pivots around
  the first marker in row-major order, while the later 6 disappears.  This is
  the only visible evidence for multi-marker selection, so that convention is
  necessarily less certain than the rotation rule.

## Hypothesis and implementation

Select the first row-major 6 as the pivot.  Start a background canvas, retain
that pivot, rotate every cell whose color is neither 0 nor 6 clockwise around
it, and clip destinations outside the original dimensions.

## Test-instance predictions

- Test 1 reproduces the first training geometry with color 8, so its four cells
  rotate to the right of the 6.
- Test 2 places the pivot on the bottom edge.  Three of four rotated 7 cells
  fall below the canvas; only the cell landing at the bottom row, column 3
  remains.
