# Blind solve notes

## Visible-example observations

- Every grid has an odd-sized frame with a full vertical line of color `4`.
- One row is marked by color `8` at the left edge, at the vertical divider,
  and at the right edge.  The divider/marker intersection is the geometric
  center of the transformation.
- The right side is initially empty background (`7`) except for the marker.
- Comparing individual cells shows that the output's right side is the left
  side rotated by 180 degrees around the central `8`.
  - In the first example, the input cell `(15, 7) = 0` becomes output
    `(1, 9) = 0` around center `(8, 8)`.
  - The input run at row 10, columns 5..7 (color `3`) becomes the output run
    at row 6, columns 9..11.
  - The left-edge `8` maps to the pre-existing right-edge `8`.

## Hypothesis

Find the vertical divider as the column with the most `4` cells and find the
center row from the `8` on that divider.  For every cell strictly left of the
divider, write it at the point reached by a half-turn around the center.  Copy
all cells, including background, so the whole left half—not just colored
objects—defines the right half.

## Implementation notes

The code leaves the divider untouched and bounds-checks reflected coordinates.
No generator, rule, reference answer, notes, or prior solution was consulted.
