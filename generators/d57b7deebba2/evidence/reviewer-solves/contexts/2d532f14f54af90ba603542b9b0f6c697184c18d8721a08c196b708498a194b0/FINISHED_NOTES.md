# Solve work log

## Prior exposure

Before this solve I had already inspected the task's generator and canonical
rule while performing the assigned repair, so this is an exposed post-repair
solve, not a blind solve.  I did not consult those sources after `prepare` and
used only `challenge.json` plus visible check feedback here.

## Revision 1

The examples show that two same-colored endpoints on a slope -1 diagonal are
joined into a solid segment.  The first training input is decisive because
color 9 occurs four times: `(0,2),(2,0)` form one anti-diagonal and
`(3,10),(6,7)` form another, and both are filled independently.  Therefore the
grouping key is `(color, r+c)`, not color alone.  For every such group with at
least two cells, copy the input and paint rows from the group's minimum to
maximum row at column `diag-row`.  Singletons remain unchanged.

I implemented that rule directly.  Remaining uncertainty before checking was
only whether a group with more than two cells should use the outermost cells;
the visible task language implied span filling, so min/max is the consistent
generalization.
