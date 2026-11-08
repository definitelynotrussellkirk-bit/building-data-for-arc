# Solve work log

## Prior exposure

I had not opened this task's generator, rule, notes, reference solution, private
labels, or audit records. I used only the visible examples produced by
`review.py blind prepare`.

## Revision 1 — projected guide columns

The blue cells occur along the outer rows and repeat columns. Treat their column
coordinates as vertical guide lines. Split gray cells into 4-connected objects;
for each object, count how many distinct blue-marked columns contain one of its
cells. Recolor the unique maximum-scoring object from gray (3) to red (2).

Evidence from the visible examples:

- Example 0: the recolored object occupies blue columns 1 and 2. The singleton
  in column 0 receives two blue markers but only one distinct guide column.
- Example 1: the recolored lower-left object occupies columns 2 and 4, while the
  upper-left distractor occupies only column 2.
- Example 2 repeats the first contrast: the target occupies columns 2 and 3,
  while the singleton occupies only column 1 despite markers above and below it.

The two visible queries also have unique maxima under this rule. Query 0 has a
single gray object, so it remains the maximum even though its score is zero.
Query 1 selects the 2×3 lower-left object because it occupies guide columns 2
and 3; every other object occupies at most one guide column.

Remaining uncertainty: the training data do not distinguish counting actual
occupied columns from counting guide columns merely inside an object's bounding
box, because those agree on every shown candidate. Actual occupancy is the more
direct projection interpretation, so the implementation uses it. Ties are not
specified by the examples; Python's stable `max` would choose the first object
in row-major order, but all shown cases have a unique maximum (or only one gray
object).
