# Visible-only solve work log

This is a human work log. I had earlier rule exposure while repairing the assigned generator, so this is not a blind episode; after this final-source solve was prepared, I did not reopen the generator, Racket rule, reference solution, private labels, or the prior solve notes.

## Hypothesis from the visible examples

Each nonzero color occurs twice. Treat those cells as opposite corners of an axis-aligned rectangle, then draw only that rectangle's border on a fresh zero grid of the same shape.

The overwrite order is visible in train example 0. Color 6 is first encountered at `(0,1)` and color 1 later at `(0,10)`. Their rectangle borders share most of the top edge, and those cells are color 1 in the output. Therefore rectangles are painted in row-major order of each color's first clue, with later rectangles overwriting earlier ones.

Train example 1 verifies thin two-row rectangles: the entire 2-by-N bounding box is border, not just the two clue cells. Train example 2 combines two crossing outer rectangles with a thin inner rectangle and supports the same blank-canvas border rule and overwrite order.

## Implementation

Scan row-major into an insertion-ordered map, compute each color's bounding box, and paint its top, bottom, left, and right edges onto an all-zero grid. A color with fewer than two cells is skipped defensively, though all three demonstrations use exactly two cells per active color.
