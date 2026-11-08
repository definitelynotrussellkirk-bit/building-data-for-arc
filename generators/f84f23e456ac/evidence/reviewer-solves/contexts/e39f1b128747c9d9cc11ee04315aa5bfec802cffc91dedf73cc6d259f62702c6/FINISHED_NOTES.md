# Solve notes

This is a human work log based only on `solve/challenge.json`.  I had earlier
rule exposure from reviewing this task's generator, so this is an exposed
post-repair solve, not a blind solve.  I did not consult the generator, Racket
source, canonical data, private labels, or a prior solution during this episode.

## Visible-example hypothesis

Each input has a compact pattern at the upper-left and zeros elsewhere.  Take
all cells from row 0 through the last row containing a nonzero and column 0
through the last column containing a nonzero; internal zeros are part of that
rectangle.  Repeat this rectangle modulo its height and width to fill the
original canvas.

Visible checks:

- Train 1 has a 2x4 rectangle and repeats every two rows/four columns.
- Train 2 has a 3x3 rectangle and repeats every three rows/columns.
- Train 3 has a 4x2 rectangle, including its all-zero second row, and repeats
  every four rows/two columns.  This rules out cropping away empty internal
  rows or tiling only nonzero cells.

The two test inputs therefore use 2x4 and 3x3 rectangles respectively.  I
implemented the direct bounding-rectangle/modulo rule as the first solve
attempt; no diagnostic or deliberately wrong revision was needed.
