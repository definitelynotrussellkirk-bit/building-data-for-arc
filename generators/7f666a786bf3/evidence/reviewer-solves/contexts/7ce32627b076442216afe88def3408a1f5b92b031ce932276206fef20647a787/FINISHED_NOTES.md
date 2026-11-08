# Solve notes

## Revision 1

Across all three visible examples, each nonzero color has sparse marker cells. The output independently replaces each color's markers by the solid axis-aligned rectangle spanning that color's minimum and maximum row and column. Background outside those rectangles remains 0. The visible rectangles are disjoint, so no overlap tie-break is needed.

I implemented exactly that per-color bounding-box fill. I did not consult the generator or Racket source during this solve; earlier rule exposure is necessarily yes because this solve follows the assigned generator review.
