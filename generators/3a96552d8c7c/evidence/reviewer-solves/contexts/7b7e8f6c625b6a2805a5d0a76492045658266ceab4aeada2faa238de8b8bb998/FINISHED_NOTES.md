# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Earlier exposure: none known; only the prepared visible examples were used.

Hypothesis: process each row independently. If its only two non-background cells
are both colour 5, recolour every background cell strictly between them to colour
3. Leave the two endpoints intact. Rows with three or more 5s are not completed,
and rows containing colour-4 cells are also left unchanged even when their outer
cells are 5. This explains every changed and unchanged row in all three examples.

Implementation directly tests the complete row inventory rather than merely taking
the leftmost/rightmost 5s, so the 3-marker and 4-blocker negative cases remain
unchanged. No column operation is suggested by the examples.
