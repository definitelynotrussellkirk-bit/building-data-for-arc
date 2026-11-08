# Solve work log

## Exposure declaration

Before this blind solve I had not opened the generator, Racket rule, canonical data,
private labels, prior solutions, notes, or audit evidence for task `c4d63d8b4567`.
I used only the visible examples printed by `python3 review.py blind prepare`.

## Revision 1 — unobstructed aligned-pair completion

Hypothesis: each pair of equal non-background markers that shares a row or column
is joined by filling the cells between them with that marker's colour, but only
when every interior cell is background. A different-coloured marker is an obstacle.

Evidence from the visible demonstrations:

- Example 0 completes both a horizontal colour-5 segment and a vertical colour-7
  segment.
- Example 2 completes the aligned colour-3 pair and leaves the unaligned colour-1
  pair unchanged.
- Example 3 completes the aligned colour-8 pair and the aligned pair among three
  colour-5 markers; the third colour-5 marker is unaligned and remains isolated.
- Example 1 distinguishes the obstacle condition: the horizontal colour-7 pair
  would pass through the colour-9 endpoint, so it is not completed, while the
  unobstructed vertical colour-9 pair is completed.

Implementation: collect nonzero positions by colour, consider every same-colour
pair, and draw a horizontal or vertical inclusive segment only when all interior
cells in the original input are zero. Segment validity is evaluated against the
original input so independently valid additions do not create order-dependent
blocking.

Predicted queries:

- Query 0: fill colour 4 down column 0 from rows 0 through 7, and colour 9 across
  row 7 from columns 2 through 9.
- Query 1: fill colour 4 across row 3 from columns 0 through 5. Do not fill the
  colour-2 vertical segment because the colour-4 endpoint at `(3, 5)` blocks its
  interior.

Remaining uncertainty: if a future grid has three or more collinear markers of the
same colour, considering every clear pair may join adjacent clear runs. This is the
most direct extension consistent with example 3 and does not affect the shown
queries.
