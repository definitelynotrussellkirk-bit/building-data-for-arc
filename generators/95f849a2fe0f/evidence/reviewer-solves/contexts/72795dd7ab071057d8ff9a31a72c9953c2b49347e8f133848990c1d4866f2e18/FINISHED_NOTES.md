# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1 — cropped-shape XOR

Before this solve I had not opened the task's generator, canonical rule, private labels,
or earlier solutions. From the three visible pairs I normalized each nonzero color by
cropping to its own bounding box. Top-left alignment explains every output exactly:
color 8 marks cells occupied by exactly one normalized shape, while overlap and joint
background stay 0. The output dimensions are the componentwise maximum of the two
cropped bounding-box dimensions. I considered subtraction in absolute input coordinates,
but the objects are spatially separated and the output consistently discards that spacing.
I added a visible-pair regression test first; it failed on the supplied stub and then
passed after implementing the normalized occupancy XOR. Remaining uncertainty: unseen
queries could in principle contain more than two colors or disconnected same-color parts,
but all visible instances have exactly two four-cell shapes and the rule uses all cells of
each color within its crop.
