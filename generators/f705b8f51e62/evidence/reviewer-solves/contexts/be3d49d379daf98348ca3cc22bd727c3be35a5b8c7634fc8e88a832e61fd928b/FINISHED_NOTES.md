# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — modal component as repair template

Observed that each training grid contains several separated monochrome objects. Two or
more objects share the same normalized shape, while one object is an incomplete copy.
The output is the repeated complete shape, recolored with the incomplete object's color
(train 2 makes the recoloring explicit: repeated objects are color 1, the damaged object
is color 5, and the output uses 5).

Implemented 4-connected monochrome component extraction, normalized each component to a
binary bounding-box mask, chose the most frequent mask as the template, and rendered that
mask using the unique non-template component's color. I considered selecting the largest
component or the rarest color, but train 1 has one incomplete line of the same color and
train 3's complete and incomplete objects overlap in size enough that repetition is the
clean invariant. Remaining uncertainty: the hidden queries might contain rotations or
multiple anomalies, but every visible example preserves orientation and has one outlier.
