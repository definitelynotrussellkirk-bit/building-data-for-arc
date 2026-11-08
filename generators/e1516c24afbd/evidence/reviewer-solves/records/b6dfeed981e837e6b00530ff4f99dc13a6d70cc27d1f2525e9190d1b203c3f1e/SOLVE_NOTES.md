# Solve notes

## Hypothesis

The input is split horizontally into two equal panels with aligned coordinates.
The output has the shape of one panel. At each output coordinate, write color 2
exactly when the corresponding cells in both the top and bottom panels are 0;
otherwise write 0.

## Visible checks

- Example 0, output `(0,1)` is 2 because top `(0,1)` and bottom `(0,1)` are both
  zero; output `(0,0)` is 0 because the bottom cell is color 4.
- Example 1 has only three 2s, each matching a coordinate where both 4x8 panels
  are zero; nonzero colors 1 and 6 act only as occupancy.
- Example 2, output row 1 columns 0 and 1 are 2 because both aligned cells are
  zero there. Every other coordinate has at least one occupied panel cell.

This is a color-invariant aligned NOR rule. I implemented it directly without
consulting any reference during this solve. I had earlier rule exposure from the
generator review, so this is not a blind solve.
