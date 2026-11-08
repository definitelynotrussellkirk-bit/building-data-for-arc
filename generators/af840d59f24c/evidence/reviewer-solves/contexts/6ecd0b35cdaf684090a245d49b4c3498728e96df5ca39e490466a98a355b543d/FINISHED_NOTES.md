# Solve work log

## Exposure and scope

This is an exposed review solve, not a blind solve. I previously reviewed this
task's generator and canonical rule and completed an earlier exposed solve at
an intermediate source. During this fresh solve I read only challenge.json and
the public README, wrote the solution below, and used the official visible-case
check. I did not consult generator source, the Racket rule, private query labels,
reference solutions, or previous solution notes during this solve phase.

This document is a concise authored account of observations, decisions, and
verification. It is not a captured internal reasoning trace.

## Revision 1

The four demonstrations keep the input dimensions and every nonzero cell.
The zero-containing columns, in increasing horizontal order, receive colors
1 through the number of those columns. Example 0 uses columns 2, 3, 5, 7;
example 1 uses 5, 7, 9, 10, 13, 15; example 2 uses 0, 2, 3, 5, 10, 14;
example 3 uses 2, 4, 5, 6, 7, 10. The two mixed-color demonstrations preserve
both nonzero colors. The solution implements this global column ranking.

No visible example required another revision. Both 10 by 10 query outputs
remain hidden; visible-case agreement does not establish their private score.
The official check completed with exit code 0: revision 1 passed 4 of 4 visible
examples. The returned private-query label is `unknown`. No revision followed.
