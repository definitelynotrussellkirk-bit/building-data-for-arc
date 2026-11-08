# Blind solve notes — 5a215cef8bd1

## Visible structure

Each input has one color-2 component and four singleton markers colored 1, 3, 4,
and 6.  The marker cells occupy the four corners of an axis-aligned rectangle.
The output is split by one all-zero central row and column into four equal square
quadrants.  The side length equals the side length of the color-2 component's
bounding box.

## Hypothesis

Crop the square bounding box around the color-2 component and treat its occupied
cells as a binary motif.  Place one copy in each output quadrant according to the
corresponding marker's spatial corner.  Recolor occupied cells to 7.  Marker color
encodes a clockwise rotation:

- 1: 0 degrees
- 3: 90 degrees
- 4: 180 degrees
- 6: 270 degrees

Evidence: train example 1 uses an asymmetric 2x2 L, making all four rotations
unambiguous.  Examples 0 and 2 agree with the same mapping and with marker-corner
placement.  The background, marker cells, and original absolute positions do not
otherwise transfer to the output.

## Implementation choices

The solution locates all 2-cells, crops their bounding box, validates that it is
square, builds the four rotations without external libraries, locates the four
markers, and writes each transformed motif into a `2n+1` output with a blank
separator row and column.  Explicit validation prevents silently producing an
answer for a materially different task structure.
