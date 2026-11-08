# Solve work log

I had not opened the repair generator, either task's Racket rule, reference
solutions, private labels, audit evidence, or prior solution explanations. I used
only the examples printed by `review.py blind prepare`.

## Revision 1 — recolor the leftmost object

Each grid contains three disjoint 4-connected objects of color 4 on background
0. The output preserves every cell except that all cells of the object with the
smallest occupied column are changed from 4 to 3.

Visible checks by example:

- Example 0: the lower-left L at columns 2–3 is left of the two objects at
  columns 5–6, and it alone becomes 3.
- Example 1: the lower vertical domino at column 8 is left of the two objects
  beginning at column 11, and it alone becomes 3.
- Example 2: the upper-left L begins at column 0, left of the horizontal and
  vertical dominoes, and it alone becomes 3.

The implementation extracts same-color 4-connected components and selects by
minimum column, with top row only as a deterministic tie-breaker. The examples do
not expose tied left edges, so that tie-break remains an implementation convention.
