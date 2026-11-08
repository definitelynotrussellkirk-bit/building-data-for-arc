# Solve work log

I had not opened this task's generator, Racket rule, reference solution, private
query labels, prior solve notes, or the assigned repair generator before starting.
I used only the visible examples in `challenge.json` / `README.md`.

## Revision 1 — extract and reorder the lower colored pieces

The input has two visually separate roles.  Sparse marks near the top provide a
left-to-right color key.  Near the bottom, each of those colors forms one larger
4-connected object.  The output crops the larger object of each color and joins
the crops in key order, inserting one zero column between consecutive objects.

Evidence from the visible examples:

- example 0's key order is 4, 7, 2, matching the three output pieces even though
  the lower input order is 2, 4, 7;
- example 1's key order is 1, 4, 5, while the lower pieces occur as 5, 4, 1;
- example 2's key order is 6, 8, 3, while the lower pieces occur as 3, 8, 6;
- output widths equal the sum of the cropped piece widths plus two separator
  columns (11, 9, and 10 respectively).

Implementation: read unique nonzero colors from the first nonempty row; find all
4-connected components of each color; select the largest component (breaking a
tie toward the lower component); crop it to its bounding box; and concatenate the
pieces with one blank column.  I top-align crops if heights ever differ, although
all visible pieces have height three.

Remaining uncertainty: the examples do not demonstrate equal-sized components,
a first key row that omits a color, or differing piece heights.  The tie-break and
top alignment are conservative extrapolations; the central observed rule does not
depend on them for the supplied examples or queries.
