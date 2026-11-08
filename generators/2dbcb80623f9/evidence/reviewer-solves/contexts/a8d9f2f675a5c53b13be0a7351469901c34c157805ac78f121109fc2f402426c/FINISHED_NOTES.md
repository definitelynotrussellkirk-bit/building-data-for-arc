# Solve work log

## Exposure statement

Before this visible-only solve I had not opened the assigned task's generator,
canonical rule, notes, reference solutions, private labels, or audit evidence. I
used only the examples printed by `python3 review.py blind prepare` and the files
inside `solve-blind/`.

## Revision 1 — connect matching colors along 45-degree diagonals

Each visible example contains three nonzero colors, each appearing exactly twice.
For pairs whose row and column separations have equal absolute value, the output
fills every cell strictly between the endpoints with that color. Pairs aligned
vertically in examples 1 and 2 remain unchanged, so the operation is specifically
for 45-degree diagonals rather than every straight line.

Implemented a general scan by color, copied the grid, and filled only two-point
pairs satisfying `abs(delta_row) == abs(delta_col) != 0`. Horizontal, vertical,
malformed, or non-paired colors are left unchanged. Remaining uncertainty is only
whether an unseen episode could contain overlapping diagonal segments; the visible
examples do not show that case, and writing each segment in turn is the most direct
extension of the demonstrated rule.
