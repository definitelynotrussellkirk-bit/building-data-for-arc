# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1

Before this solve I had not seen this task's generator, Racket rule, reference
solution, private labels, or any earlier explanation.

Hypothesis: each nonzero 4-connected monochrome object is cropped without
rotation, then the objects are stacked vertically in decreasing bounding-box
width.  Each crop is left-aligned to the widest object's width, with one blank
row between adjacent objects.  The three demonstrations consistently order the
width-4 five-cell shape, width-2 rectangle, and width-1 line this way while
preserving their colors and orientations.

Probe: I compared bounding boxes and reconstructed all three visible outputs.
Remaining uncertainty is tie-breaking for equal-width objects; I use their
original top-to-bottom, then left-to-right order because the visible examples do
not constrain ties.  Background is inferred as the most frequent color.
