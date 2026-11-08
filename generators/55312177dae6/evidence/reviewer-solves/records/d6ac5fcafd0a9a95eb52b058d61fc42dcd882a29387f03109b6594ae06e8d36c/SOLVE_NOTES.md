# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — repeated-family/rightmost/clockwise hypothesis

Earlier exposure: none to this task's generator, rule, notes, solutions, audit records, or private labels. I read only `solve-blind/challenge.json` after preparation.

Observed that each input contains several 4-connected objects. Exactly one geometric shape family repeats when rotations/reflections are treated as equivalent. The output is the rightmost member of that repeated family, cropped, rotated 90 degrees clockwise, and recolored from 1 to 8. This accounts for all four visible examples: the repeated family sizes are 3, 2, 2, and 2 respectively, while distractors are noncongruent.

Implementation probe: extract nonzero 4-connected components, canonicalize each over all eight dihedral transforms, select the most frequent repeated family, choose its member with greatest right edge, rotate clockwise, and recolor. Remaining uncertainty is only tie-breaking if a hidden instance contains multiple repeated families or identical right edges; the visible examples do not exercise that case.
