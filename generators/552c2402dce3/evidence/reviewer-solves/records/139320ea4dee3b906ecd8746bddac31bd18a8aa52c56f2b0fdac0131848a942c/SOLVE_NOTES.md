# Solve work log

During this solve I used only `solve/challenge.json`, my own Python, and the
visible-only check command. I did not reopen the Racket rule, generator source,
reference solution, or private labels. Earlier rule exposure is **yes** because
I reviewed and repaired this generator before this fresh solve.

## Revision 1

Hypothesis: inspect every 2×2 window in the unchanged input. When a window has
exactly three cyan (`8`) cells and one black (`0`) cell, fill the black corner
with cyan. All other structures are distractors and remain unchanged, including
a three-cell line, an already complete 2×2 square, and a larger connected shape
with a tail. Detection must use the original grid rather than newly filled cells
so one completion cannot cascade into another.

Probe: added a regression test over all four visible training pairs. The test
failed on the untouched template with `NotImplementedError`, as expected.

Implementation: copied the input, enumerated all adjacent 2×2 windows in the
original copy, and filled the unique zero only when the multiset was exactly
`{8, 8, 8, 0}`. The visible-example regression then passed all four pairs.
Remaining uncertainty: the examples use only colors 0 and 8, but the exact
multiset guard deliberately leaves any differently colored window unchanged.
