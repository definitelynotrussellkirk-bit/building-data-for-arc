# Solve work log

I had not seen this task's generator, Racket rule, private labels, or prior solution before the blind episode. I used only the visible examples printed by `review.py blind prepare`.

## Revision 1 — harness baseline

I first kept the supplied `NotImplementedError` template and ran the checker as a diagnostic probe. It errored on all four visible examples, confirming that the solve harness was exercising this file before I wrote the rule.

## Revision 2 — Manhattan Voronoi fill inside the 8 rectangle

The 8-valued cells mark the bounding rectangle, sometimes as a complete border and sometimes only as four corners. I converted each visible example to coordinates relative to that rectangle's strict interior.

The first two examples have seeds at relative positions `(0,0)` and `(2,4)`. Their diagonal zero seam consists exactly of cells whose Manhattan distances to the two differently colored seeds are equal. On either side, every cell takes the color of the uniquely closest seed. The last two examples confirm how repeated seeds of one color work: distance is to the nearest seed cell, and a tie between the repeated-color region and the other color remains zero. A tie among multiple seeds of the same color is harmless and should still yield that color.

Implementation hypothesis:

1. Find the minimum/maximum row and column containing color 8.
2. Preserve the whole input outside and on that rectangle.
3. Treat every nonzero, non-8 interior cell as a colored seed.
4. For each zero interior cell, compute Manhattan distance to all seeds. Fill it only when all minimum-distance seeds have one color; otherwise leave it zero.

Remaining uncertainty: the examples do not show malformed/multiple 8 frames or a frame with no seeds. The implementation conservatively returns an unchanged copy without any 8 cells and leaves an empty framed interior unchanged.
