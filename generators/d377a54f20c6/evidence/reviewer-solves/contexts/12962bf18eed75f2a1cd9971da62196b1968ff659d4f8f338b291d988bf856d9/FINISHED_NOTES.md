# Solve work log

I had not opened task `d377a54f20c6`'s generator, Racket rule, notes, solutions,
audit records, or private labels before this blind solve. I used only
`solve-blind/challenge.json` and local reasoning.

## Visible-example observations

- Every input contains a solid nonzero rectangle on a zero background. One or
  more cells inside the rectangle use a second, rare color.
- Every output retains only the rectangle's one-cell outer frame in the common
  rectangle color. All other former fill cells become zero except for a pattern
  in the rare color.
- In interior coordinates, that pattern starts at all four interior corners and
  advances inward at 45 degrees. When the interior is not a same-parity square,
  the four arms meet in a filled central row/column/rectangle rather than a
  single cell.
- The rare cells' *positions* in the input differ across examples and do not
  coincide consistently with output cells. Their stable role appears to be
  selecting the drawing color, not locating the drawing.

## Hypothesis and implementation

Let the non-background bounding box be the rectangle. The most frequent nonzero
color inside it is the frame color; the other color is the accent. For an
interior of height `H` and width `W`, set
`k = floor((min(H, W) - 1) / 2)`. Draw the four corner diagonals for offsets
`0 .. k-1`, then fill the residual central rectangle
`rows k .. H-k-1, columns k .. W-k-1` in the accent color.

This reproduces the observed 8x12 interior as three diagonal steps plus a 2x6
center, the 12x8 interior as three steps plus a 6x2 center, and the 8x7 interior
as three steps plus a 2x1 center.

## Remaining uncertainty

The visible data strongly supports marker position being irrelevant, but it does
not prove whether unusual lessons might encode meaning in marker count or
position. The submitted solver follows the common rule shared by all three
examples and handles arbitrary rectangular dimensions, including thin interiors.
