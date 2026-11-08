# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — every third horizontal block

Earlier exposure: I had not opened this task's generator, rule, notes, solution,
or private labels. I had only seen the visible examples printed by `blind prepare`.

Observation: every puzzle is a vertical sequence of monochrome horizontal
patterns. A pattern can occupy one or more identical consecutive rows. In all
three demonstrations, output color 2 replaces exactly block indices
0, 3, 6, ... while zeros and all other blocks remain unchanged.

Probe: I enumerated maximal runs of identical rows in each visible example and
checked the changed runs. The changed run positions were 0/3/6/9/12/15 in train
0, 0/3/6 in train 1, and 0/3/6/9 in train 2. This ruled out earlier tentative
ideas based on pixel count, symmetry, or color identity.

Implementation: copy the grid, scan maximal identical-row runs, and replace each
nonzero cell in every third run (starting at the first) with 2. Remaining
uncertainty: an unseen input could use adjacent same-colored blocks with different
row masks; exact-row run segmentation still keeps those blocks separate.
