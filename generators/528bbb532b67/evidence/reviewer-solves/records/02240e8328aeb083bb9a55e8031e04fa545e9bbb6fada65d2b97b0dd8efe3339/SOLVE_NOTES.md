# Solve work log

## Exposure declaration before solving

Before opening `solve-blind/challenge.json`, I had read only the packet-level
instructions, repository overview, assignment text, and runtime setup output. I
did not open task `528bbb532b67`'s generator, canonical rule, notes, prior solve
records, private labels, or reference solution.

## Revision 1 — vertical reflection inside the azure frame

All three demonstrations contain one rectangular border of color 8. The
non-border colored cells occupy the left side of that rectangle, and the output
keeps them while adding their horizontal reflections across the rectangle's
vertical axis. The axis can lie on a column (odd interior width) or between two
columns (even interior width); using `mirror_col = left_border + right_border -
col` handles both. Existing center-axis cells remain unchanged. I rejected a
"copy each row to the right edge" interpretation because the second and third
examples preserve exact offsets and multiple colors, which specifically matches
reflection.

Implementation: locate the extrema of all color-8 cells, copy the grid, and
mirror every nonzero, non-8 cell lying strictly between the two vertical border
columns. Remaining uncertainty: the generated task appears to contain exactly
one clean frame, as in every visible example; the solution intentionally does
not try to disambiguate multiple unrelated color-8 objects.
