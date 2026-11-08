# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1

Earlier exposure: none known. I had not opened the task's generator, rule, notes,
solutions, or labels. I used only the prepared visible examples.

Hypothesis: the background is the dominant color. Non-background shapes sit in
corners. A color represented by two or more disconnected corner objects is the
active color; every object of that color moves diagonally inward. Its vertical
shift equals its own bounding-box height and its horizontal shift equals its own
bounding-box width, with signs determined by the touched corner. Objects whose
color occurs only once stay fixed.

Evidence: this explains the four 3x3 blocks in example 0; the three color-6
objects but not the lone color-5 block in example 1; only the paired color-3
points in example 2; and both repeated colors with different object sizes in
example 3. I implemented monochrome 4-connected components and simultaneous
clear-then-place movement. Main uncertainty: unseen irregular objects, though
bounding-box-sized inward translation is the simplest rule matching all visible
examples.
