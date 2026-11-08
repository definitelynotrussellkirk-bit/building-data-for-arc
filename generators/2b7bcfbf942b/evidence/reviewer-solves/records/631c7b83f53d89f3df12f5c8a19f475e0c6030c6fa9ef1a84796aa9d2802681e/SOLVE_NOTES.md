# Blind solve notes — 2b7bcfbf942b

## Visible pattern hypothesis

Each nonzero connected shape specifies the color and bounding rectangle of a
framed checkerboard.  Some inputs already show a complete rectangular outline,
some omit the final horizontal side, and one uses a centered cross.  In every
training output, the bounding box becomes a solid colored border.  Interior
cells alternate between the component color and background, with local position
`(1, 1)` colored; equivalently, an interior cell is colored when its row-plus-
column offset from the bounding-box origin is even.

## Implementation choice

Find 4-connected components independently by color, compute each bounding box,
and redraw only that box using the border/parity rule.  Component-wise handling
also permits multiple differently colored shapes in one grid, as shown by the
second training example and first query.

## Expected query behavior

- Query 1: fill the interiors of the upper green rectangle and lower maroon
  rectangle with the same alternating pattern while preserving solid borders.
- Query 2: complete the missing bottom edge of the green rectangle and fill its
  interior checkerboard.
