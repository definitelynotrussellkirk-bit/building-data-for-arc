# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — row key recolors gray cells

Observed that every training row containing a nonzero color other than 8 uses that
color to replace all 8 cells in the same row. Rows containing 8 but no colored key
leave the 8 unchanged. The training keys happen to be in column 0; test 1 adds a
second colored cell to the right, so I use the leftmost nonzero/non-8 cell as the
row key rather than requiring it to be the only colored cell. This predicts the
ambiguous midpoint 8 in test 1 row 0 becomes 7 (the left key), while existing
non-8 colors remain unchanged. Alternative considered: nearest colored cell, but
that is underdetermined on the midpoint and is not needed to explain any example.
