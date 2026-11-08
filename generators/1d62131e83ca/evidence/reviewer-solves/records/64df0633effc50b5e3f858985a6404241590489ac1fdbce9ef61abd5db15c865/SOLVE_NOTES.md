# Solve work log

## Exposure record

Before this blind solve I had not opened the assigned repair generator, this task's
generator, any Racket rule, canonical answer, prior solution, audit record, or private
query label. I used only the visible examples produced by `review.py blind prepare`.

## Revision 1 — diagonal rays from the two 2×2 anchors

Across all three visible pairs, the four cells of color 1 form a 2×2 square and the
four cells of color 2 form another 2×2 square. The output preserves both squares.
It adds a northwest diagonal of color 1 beginning one cell northwest of color 1's
top-left cell, continuing until either the top or left boundary. It independently
adds a southeast diagonal of color 2 beginning one cell southeast of color 2's
bottom-right cell, continuing until either the bottom or right boundary.

I compared the added coordinates in each visible pair:

- example 0: color 1 adds `(2,3),(1,2),(0,1)` and color 2 adds
  `(10,4),(11,5),(12,6),(13,7)`;
- example 1: color 1 adds `(5,1),(4,0)` and color 2 adds `(10,2),(11,3)`;
- example 2: color 1 adds `(6,2),(5,1),(4,0)` and color 2 adds `(11,8),(12,9)`.

This rejects alternatives based on the relative positions of the two squares: the
same color-specific directions hold even though their horizontal ordering changes.
I wrote one direct implementation that locates all color-1 and color-2 cells, uses
the extrema identifying the corresponding square corners, and paints those two
rays on a copy of the input. A local visible-example regression test failed first
on the template's `NotImplementedError`, then passed for all three examples after
this implementation. Remaining uncertainty is limited to unseen malformed inputs
or collisions, neither of which appears in the visible task distribution.
