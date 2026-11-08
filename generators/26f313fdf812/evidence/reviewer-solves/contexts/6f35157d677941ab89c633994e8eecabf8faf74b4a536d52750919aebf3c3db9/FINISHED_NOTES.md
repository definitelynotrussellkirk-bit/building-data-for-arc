# Solve work log

## Exposure statement

Before this solve I had read only the packet-level instructions and the visible
presentation produced by `python3 review.py blind prepare`. I did not inspect the
blind task's generator, rule, canonical record, prior notes, solutions, labels,
or audit evidence.

## Revision 1 — pairwise object-area comparison

The number of output rows/columns equals the number of non-background objects.
The diagonal is always color 1, and each off-diagonal pair is complementary:
one direction is 2 and the reverse direction is 3. This suggested a pairwise
comparison table.

Counting cells showed that 2 means “the row object has greater area,” 3 means
“the row object has smaller area,” and 1 means equal area. The initially
ambiguous ordering became clear in examples 1 and 3: objects are ordered by the
top-left corner of their full bounding box, not by the first occupied cell in
row-major order. For example, the long upper object in example 1 has bounding
box corner `(0, 1)`, so it precedes the two-cell object at `(0, 3)` even though
its first occupied cell occurs later.

I implemented monochrome 4-connected component extraction, sorted components by
`(minimum row, minimum column)`, and emitted the area-comparison matrix. Using
components rather than merely grouping by color keeps the program faithful to
the visible notion of separate objects if a color is ever reused.

Predicted query object areas in bounding-box order:

- Query 0: `[4, 9, 2, 3, 4]`
- Query 1: `[7, 2, 8, 4, 9]`

Remaining uncertainty: the visible examples use one object per nonzero color, so
same-colored disconnected components are not directly demonstrated. Treating
them as separate objects is the least-assumptive geometric interpretation.
