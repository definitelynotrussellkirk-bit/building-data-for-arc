# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

The output dimensions and the number of 1-cells are unchanged. Comparing each
column independently shows that its 1-cells are compacted against the bottom:
training example 1 has three 1s in columns 0 and 7, which become rows 5--7,
while the single 1 in column 3 moves to the last row. The same column-count rule
exactly explains the other two examples. I therefore implemented vertical
gravity independently in each column, preserving top-to-bottom order for the
more general case of multiple nonzero colors.

Predicted tests:
- test 1: row 4 has 1s at columns 1, 4, 5; the last row is all 1s.
- test 2: row 5 has 1s at columns 1 and 4; the last row is all 1s.

Remaining uncertainty: examples use only color 1, so order preservation among
multiple colors is not observable. It is the least destructive generalization.
