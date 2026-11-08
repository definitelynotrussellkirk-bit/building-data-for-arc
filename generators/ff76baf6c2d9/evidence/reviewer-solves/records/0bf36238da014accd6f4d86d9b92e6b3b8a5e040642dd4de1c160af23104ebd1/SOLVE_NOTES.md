# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — copy each completed motif to matching singleton markers

Visible examples suggest that a one-cell marker color identifies a nearby multicolor
motif elsewhere in the same grid.  I will find 8-connected nonzero components,
use a marker color that also occurs as a singleton as the anchor, and stamp the
other cells at every singleton of that color.  First try the observed orientation;
if it would leave the grid or overwrite a nonzero cell, try reflections/rotations.
This should explain the forced horizontal reflection in train 2.  Remaining
uncertainty: train 0's color-2 motif is reflected even though its observed
orientation would also fit at the target, so a boundary-normalization convention
may be present.

## Revision 2 — apply one dihedral transform to the whole motif

The first implementation chose a transform from a per-offset de-duplicated list,
so symmetric offsets could receive different transform indices.  That distorted
the motif and caused train 2 to fail even though a horizontal reflection should
have fit.  I replaced this with a fixed eight-transform table shared by every
cell.  Train 1 and train 2 now match exactly; train 0 still isolates the unresolved
boundary-normalization behavior for the color-2 motif.
