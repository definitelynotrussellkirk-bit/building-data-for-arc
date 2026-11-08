# Solve work log

## Exposure

I had not opened this task's generator, canonical rule, reference solution,
private labels, or prior solution notes. I used only the visible examples emitted
by `python3 review.py blind prepare` and the solve workspace files.

## Revision 1 — diagonal duplication plus horizontal separators

Observed structure:

- Every output is exactly twice the input height and width.
- The input is copied unchanged into the top-left quadrant and again into the
  bottom-right quadrant; the other two quadrants stay background zero.
- Some completely zero input rows become full-width color-3 rows in both copies.
- The final zero row in train example 2 stays zero, unlike the interior/leading
  zero rows. This suggests color 3 marks blank rows that occur before remaining
  colored content, while trailing blank padding is not a separator.

Implemented that rule directly: find the last nonzero row, mark each all-zero row
strictly before it as color 3 across the full doubled width, and place the two
input copies diagonally.

Remaining uncertainty: query 1 has two consecutive leading blank rows, a case not
shown in training. I apply the same separator rule to both because both occur
before colored content. A narrower alternative would mark only one boundary row,
but nothing in the demonstrations identifies which one, while the per-row rule
matches every shown output and treats each blank row consistently.
