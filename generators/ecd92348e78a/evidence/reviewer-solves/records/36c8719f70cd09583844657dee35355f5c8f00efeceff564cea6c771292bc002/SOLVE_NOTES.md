# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, canonical rule, reference solution,
private labels, audit records, or any generator assigned for repair.  I used only
the visible examples printed by `python3 review.py blind prepare` and the files in
`solve-blind/`.

## Revision 1 — height histogram of colored objects

The visible examples contain one object per nonzero color.  Each output column is
a top-aligned solid vertical bar in that color.  Its height equals the number of
input rows containing the color (equivalently the visible object's vertical
extent in these examples), and columns are ordered from greatest height to least.
The output has one column per color and as many rows as the tallest object.

Checks against the demonstrations:

- Example 0 has heights 5, 4, 3, 1 for colors 5, 6, 4, 1, matching the four
  output columns.
- Example 1 has heights 6, 5, 4 for colors 7, 1, 5.
- Example 2 has heights 5 and 3 for colors 6 and 3.

For the two queries this predicts orders `(6, 3, 4)` with heights `(5, 4, 3)`
and `(5, 8, 7)` with heights `(6, 5, 4)`.  I implemented the row-support rule,
with color order as a deterministic tie-breaker if equal heights occur.  The
visible examples do not establish the intended tie policy, nor distinguish row
support from bounding-box height for disconnected same-color cells; those are
remaining uncertainties.
