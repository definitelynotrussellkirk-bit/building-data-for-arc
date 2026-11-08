# Blind solve notes — 5295bc5ff1cb

Human work log based only on `challenge.json`.

## Hypothesis

The bottom and right monochrome strips are an L-shaped padding area, not part of
the motif.  The non-padding top-left rectangle is a truncated periodic texture.
Every training output:

1. shifts that texture one cell to the left (output column 0 equals input motif
   column 1), and
2. continues the shifted periodic texture through the former right and bottom
   padding to restore a full rectangular pattern.

Checks against the three demonstrations:

- 3-column texture: `7,2,2` becomes `2,2,7` after one left shift.
- checkerboard: `5,4,5,...` becomes `4,5,4,...`.
- 3-column texture: `6,5,5` becomes `5,5,6`.

The row phases also continue periodically into the removed bottom strip.  I infer
the smallest row and column periods consistent with every observed active cell,
then generate the full original dimensions using `(row mod row_period,
(column + 1) mod column_period)`.

## Edge handling

The padding color is the bottom-right color.  I remove only complete trailing
rows and columns of that color, so isolated occurrences would not shrink the
motif.  Empty inputs are returned empty.
