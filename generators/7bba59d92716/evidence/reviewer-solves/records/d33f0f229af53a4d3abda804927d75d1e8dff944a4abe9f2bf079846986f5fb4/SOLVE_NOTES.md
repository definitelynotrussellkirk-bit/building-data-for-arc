# Solve work log

Earlier exposure before this blind episode: none to task `7bba59d92716`'s rule,
generator, private labels, or prior solution notes. I used only the public grids
printed by `review.py blind prepare`.

## Revision 1 — rotated exemplar matching

Hypothesis: the isolated horizontal run of five color-1 cells on the top row is
an exemplar object.  In the rest of the grid, every 4-connected color-1 object
that is exactly the same straight five-cell line under rotation has its center
cell recolored to 2.  Other colors are markers/clutter and do not join the
color-1 component.  Bent objects, branched objects, and straight runs of the
wrong length remain unchanged.

Checks by hand against the visible examples:

- Example 0 changes exactly the three vertical length-5 components and excludes
  a length-6 line and an L-shaped component.
- Example 1 changes the two vertical length-5 components and excludes the cross,
  a length-3 line, and unrelated colored markers.
- Example 2 changes the three vertical length-5 components and excludes a
  length-6 line and a length-5 stem with a one-cell branch.

Implementation: enumerate 4-connected components of color 1, select the straight
component touching row 0 as the exemplar, and recolor the middle cell of every
other straight contiguous component with the same cardinality.  Remaining
uncertainty: the visible distribution always places the exemplar on row 0; the
implementation follows that observable convention rather than inventing a more
general selector.
