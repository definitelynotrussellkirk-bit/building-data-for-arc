# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1 — exposed confirmation solve

Earlier exposure is **yes**: generator repair work had already revealed the intended
rule, so this is not an independent blind inference. During this solve I did not open
the generator, Racket source, private outputs, or prior explanations; I used only the
prepared visible examples.

The three demonstrations consistently show a one-sided line of color 2 attached to a
single color-5 pivot. The source cells become 3, while the same relative offsets are
rotated 90 degrees clockwise around the pivot and painted 2. The pivot remains 5 and
all other cells remain 0. I implemented this directly using offset mapping
`(dr, dc) -> (dc, -dr)` in row/column coordinates. The visible examples cover left,
right, and up source directions and lengths 4, 4, and 2; the two queries exercise down
length 4 and left length 2. No alternative remained plausible from these examples.
