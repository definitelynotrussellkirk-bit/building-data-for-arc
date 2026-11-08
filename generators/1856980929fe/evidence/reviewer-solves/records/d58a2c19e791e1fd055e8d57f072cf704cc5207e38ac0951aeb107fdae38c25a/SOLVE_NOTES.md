# Post-repair solve notes

This is a human work log from the visible examples. I had already studied the
assigned task while repairing its generator, so the final declaration must say
`earlier-exposure yes`; during this solve episode I did not reopen the generator,
Racket source, reference solutions, or private labels.

## Visible-example observations

- Every output retains all input cells and adds only color 3.
- Each input object is a filled rectangle. Its own height and width determine a
  repeated displacement.
- For example, the 2x4 rectangle at rows 4–5, columns 9–12 in training example 2
  produces 2x4 copies beginning at `(6,5)` and `(6,13)`, then `(8,1)` and
  `(8,17)`: offsets `(k*2, ±k*4)`.
- Copies continue downward until their rows leave the canvas. Copies that cross a
  side or bottom boundary are clipped, as shown by the two-cell sliver at column
  0 and the one-column sliver at column 25 in that example.
- Each seed rectangle acts independently; overlapping copies are simply unioned.

## Hypothesis implemented

Find every 4-connected nonzero seed rectangle. For a rectangle with top-left
`(r,c)`, height `h`, and width `w`, preserve it and paint full copies at
`(r+k*h, c-k*w)` and `(r+k*h, c+k*w)` for every positive integer `k` while the
copy can still intersect the grid vertically. Clip each copy to the canvas.

The implementation uses only the visible challenge and applies the same rule to
all seed rectangles, including multiple sizes in one grid.
