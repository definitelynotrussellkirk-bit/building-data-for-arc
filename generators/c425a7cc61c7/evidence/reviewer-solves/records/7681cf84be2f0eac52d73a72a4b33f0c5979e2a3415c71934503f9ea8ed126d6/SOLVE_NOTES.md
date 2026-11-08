# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1

Before this blind step I had not opened task `c425a7cc61c7`'s generator, rule,
notes, solutions, labels, or audit records. I had only read the packet-level
instructions and the generated visible challenge.

Hypothesis: the nonzero top-left cell is a color key. Ignore that one-cell key,
find the other 4-connected object of the same color, crop its bounding box, and
rotate the crop 90 degrees clockwise. This explains all three visible pairs:
the keyed 7 and keyed 4 L-like objects become their shown clockwise rotations,
and the keyed 1 rectangle changes from 2x3 to 3x2. Other colored objects are
distractors. I implemented connected-component selection rather than selecting
all cells of the color, so the corner key is excluded explicitly. Remaining
uncertainty: unseen inputs could contain more than one non-corner component of
the keyed color; I choose the largest, which is the least restrictive extension
of the examples.
