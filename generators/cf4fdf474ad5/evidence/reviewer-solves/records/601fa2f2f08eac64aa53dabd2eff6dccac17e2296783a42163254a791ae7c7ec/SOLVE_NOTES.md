# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1 — lower-left component extraction

Earlier exposure before this solve: none. I had not opened this task's generator,
canonical rule, reference solution, private labels, notes, or audit evidence.

Visible examples each contain four 4-connected, zero-separated blocks made only
of colors 3 and 8. The labelled output exactly equals the lower-left block, with
all surrounding zero padding removed. I checked this directly against all rows of
the three labelled outputs. The other blocks differ in shape (upper-left is wider,
upper-right is taller, lower-right is smaller), so selecting by a fixed output
shape would overfit; selecting by relative position is the common relation.

Implementation: enumerate 4-connected nonzero components, compute bounding boxes,
choose the component with greatest top row and, on a tie, smallest left column,
then return its bounding-box crop. A temporary local regression first failed on
the unimplemented template, then covered all three visible pairs and a translated
synthetic four-block layout. Remaining uncertainty: the hidden queries could in
principle contain irregular nonzero components, but bounding-box cropping matches
the visible presentation and preserves any internal pattern.
