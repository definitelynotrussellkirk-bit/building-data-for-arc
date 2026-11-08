# Solve work log

This is a human work log from the visible examples, not a token-level model trace.
I had earlier exposure to the task's intended rule while repairing the generator, so
this is an exposed solve; during this episode I kept the generator, Racket source,
reference solutions, private labels, and earlier explanations closed.

## Revision 1 — row-major transparent overlay

Visible-example observations:

- Each input has one dominant background color filling the separators.
- The non-background cells form several disjoint, equally sized solid rectangles;
  zero is part of a rectangle rather than the separator color.
- The output has exactly the common rectangle dimensions.
- Reading rectangles by top-left coordinate, each output cell is the first nonzero
  value at that local coordinate. If all rectangles contain zero there, the output
  remains zero.

Manual probes on the visible examples:

- Train 1, output row 2 column 3: the first two rectangles have zero and the third
  has 7, matching output 7.
- Train 2, output row 1 column 2: the first three rectangles have zero and the
  fourth has 8, matching output 8.
- Train 3 contains collisions where an earlier nonzero masks a later different
  nonzero, supporting priority rather than an unordered union.

Implementation plan: infer the background as the most frequent grid value, find
4-neighbour connected components of all non-background cells, require each
component to fill its bounding rectangle, sort rectangles row-major, and overlay
with zero transparent and first visible value winning. Remaining uncertainty is
limited to malformed inputs outside the visible lesson structure; the two test
queries visibly use the same separated-rectangle format.
