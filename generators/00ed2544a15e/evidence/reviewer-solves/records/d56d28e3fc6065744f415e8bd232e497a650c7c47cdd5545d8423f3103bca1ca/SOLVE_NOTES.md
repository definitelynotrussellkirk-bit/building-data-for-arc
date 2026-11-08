# Visible-only blind solve: 00ed2544a15e

## Exposure
I saw only the assignment, general packet/workflow instructions, and the public
challenge presentation. I did not open any task generator, canonical rule,
task notes, answer file, reference solution, or audit evidence before this solve.
I read generic ARC-DESIGN/PARAMETRIC guidance while initially inspecting the
packet; it contained no task-specific solution information.

## Hypothesis 1
Keep every original nonzero cell. Connect consecutive red (2) endpoints in
each row and column using azure (8), but only when the entire intervening gap
is zero in the original input. A differently colored cell blocks the whole gap.
Use the original input for both directions so drawn lines cannot become blockers.

Visible evidence: example 0 (9 by 13) connects the three row-3 endpoints and
the column-6 endpoints. Example 1 (9 by 12) leaves the row-2 gap unfilled because
the 7 lies between its red endpoints, while joining the vertical red line.
Example 2 (8 by 13) similarly blocks the left row-4 gap using the 5 and fills
the clear right and vertical gaps. All visible outputs retain the input shape.

No failed hypothesis has been invented. The first implementation encodes this
single rule and is submitted to the visible-only checker. The two masked query
answers will not be inspected or claimed correct here.
