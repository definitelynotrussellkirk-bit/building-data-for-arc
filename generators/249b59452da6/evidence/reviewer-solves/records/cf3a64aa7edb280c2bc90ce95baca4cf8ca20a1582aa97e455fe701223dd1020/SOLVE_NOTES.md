# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Earlier exposure: none. I had not opened this task's generator, rule, notes,
solutions, audit records, or private labels.

Hypothesis from the three visible demonstrations: inspect every 2×2 window in
the original grid. When exactly two red cells (color 2) occupy opposite diagonal
corners and the other two corners are background 0, recolor those two background
corners green (color 3). Other colors block a completion. Apply all detections
from the original input rather than cascading from newly written green cells.

Evidence: this accounts for all added green cells in every demonstration. It
also explains why nearby marker-colored cells and 3-of-4 occupied 2×2 windows
are left unchanged. A temporary visible-example test failed on the untouched
NotImplementedError template before this implementation was written.

Alternatives rejected: copying a special-colored exemplar object, completing
whole connected components, or filling every pair of diagonal red cells. Those
rules do not explain why windows with a third occupied corner remain unchanged.
Remaining uncertainty is limited to unseen domain cases such as ragged grids;
the visible tasks are rectangular.
