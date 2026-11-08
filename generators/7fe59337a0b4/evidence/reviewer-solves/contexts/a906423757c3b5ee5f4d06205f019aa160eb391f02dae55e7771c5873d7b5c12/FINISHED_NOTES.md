# Solve notes — 7fe59337a0b4

## Visible-only hypothesis

Each input contains one color-9 marker and one monochrome asymmetric motif. The
output discards the motif's original position and builds a four-copy compass
collage around the marker:

- north: the cropped motif in its original orientation;
- east: one 90-degree clockwise rotation;
- south: 180 degrees;
- west: 270 degrees clockwise.

There is a one-cell gap between the marker and each copy. The output keeps the
same canvas dimensions and the color-9 marker.

## Checks made before revision 1

The 3-cell L examples determine the rotation direction. The 4- and 5-cell
examples show that the entire cropped matrix, including internal zero cells,
is rotated rather than merely moving an unordered set. Inputs from north,
east, south, west, and diagonal source positions all produce the same centered
collage, so source location is not part of the output geometry.

## Exposure record

I had already inspected the generator while performing the assigned repair, so
this is an exposed post-repair solve, not a blind solve. I did not consult the
Racket source, private labels, or reference solution during this solve episode.
