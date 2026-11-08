# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — horizontal one-cell bridge

Earlier exposure: none. Before this solve I had not opened this task's generator,
Racket rule, reference solution, private labels, audit records, or prior notes.

Hypothesis: every changed cell is a zero lying horizontally between two equal
nonzero cells exactly two columns apart. The operation is local and pairwise:
`c,0,c -> c,c,c`. Chained pairs explain the longer filled spans in train 0 row 0
and train 2 row 0. Larger horizontal gaps, vertical repetitions, diagonals, and
singletons remain unchanged.

Visible probes:
- Train 0 adds color 2 at columns 2,4,6 in row 0 and color 5 at column 2 in row 1.
- Train 1 adds color 7 only at row 4 column 3.
- Train 2 adds color 3 at row 0 columns 4 and 6.
These are exactly the zero centers of equal-color distance-two pairs, with no
extra changes predicted.

Implementation copies the grid and scans each row for those centers. Remaining
uncertainty: the examples do not show a row containing overlapping candidates of
different colors, but the local rule gives an unambiguous result there.
