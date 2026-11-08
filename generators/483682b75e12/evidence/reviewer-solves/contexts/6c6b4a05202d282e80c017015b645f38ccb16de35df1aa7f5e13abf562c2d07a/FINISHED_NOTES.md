# Solve work log

## Exposure record

I had not seen this task's generator, Racket rule, reference solution, private
labels, or prior solve notes before this attempt.  I used only the visible grids
in this solve packet.

## Attempt 1 — object area controls upward displacement

Across the three visible examples, every non-background object keeps its shape,
color, and columns while moving upward.  The displacement equals the number of
cells in that 4-connected monochrome object:

- each 2-cell vertical domino in example 0 moves up 2 rows;
- each 3-cell horizontal bar in example 1 moves up 3 rows;
- in example 2, the singleton moves up 1, the domino moves up 2, and the
  4-cell T moves up 4.

The uniform color-8 bottom row stays fixed and color 7 is the background.  My
program therefore finds monochrome 4-connected components excluding the fixed
bottom row, clears them, and translates each upward by its area.  A remaining
uncertainty is whether same-colored diagonally touching cells should be one
object; the examples support ordinary 4-connectivity rather than diagonal
connectivity.
