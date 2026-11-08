# Solve work log

## Visible evidence

All three demonstrations preserve dimensions, zeros, and isolated non-green key cells.  Every 4-connected green (3) component is recolored uniformly.  The new color is read from the nonzero cell one row above the component's bounding-box top and at the bounding-box left column.

The examples deliberately include components whose upper-left bounding-box cell is zero.  For those components, using the cell above the first occupied cell on the top row would select the wrong column; the demonstrated output instead follows the bounding-box-left key.  Different components in the same grid use different key colors, so a single global key is also ruled out.

## Revision 1

Implemented independent 4-connected component discovery for color 3.  For each component, compute `(top, left)` from its bounding box, read `grid[top-1][left]`, and replace only that component's cells.  Preserve every other cell and the original dimensions.

Earlier rule exposure is **yes** because this solve follows generator review, but I did not inspect the generator, Racket source, reference solution, or private labels during this solve episode.
