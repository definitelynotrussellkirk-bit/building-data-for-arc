# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — hollow solid rectangles

Observed that every nonzero object in all three demonstrations is a filled,
axis-aligned rectangle. The output preserves each rectangle's outermost row and
column while replacing only its strict interior with background 0. Repeated
colors can form multiple spatially separated rectangles, so the implementation
uses four-connected monochrome components rather than one bounding box per color.

Before implementation I ran a visible-example assertion against the template;
it failed with the expected `NotImplementedError`. I then implemented component
extraction, verified that a component exactly fills its bounding box, and hollowed
only strict interior cells. The rectangle guard is conservative: an unexpected
non-rectangular object is left unchanged rather than damaged. Remaining
uncertainty is limited to whether diagonally touching same-color rectangles are
intended as distinct objects; four-connectivity treats them as distinct, which is
the usual ARC object convention and is consistent with the visible examples.
