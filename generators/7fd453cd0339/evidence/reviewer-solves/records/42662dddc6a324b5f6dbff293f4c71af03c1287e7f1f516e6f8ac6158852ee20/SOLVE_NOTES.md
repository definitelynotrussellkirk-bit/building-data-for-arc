# Visible-only solve: 7fd453cd0339

This is an authored work summary, not a captured token-level model trace.
Earlier exposure: none. No generator, Racket rule, canonical helper, private
answer, previous solution, or audit record was opened for this task.

## Evidence and selected hypothesis

The three visible demonstrations preserve their input dimensions: 7 x 8,
13 x 14, and 7 x 9. Each separate nonzero rectangle becomes its corner cells
on the same zero background. The 13 x 14 demonstration contains multiple
disconnected rectangles of color 4, so components must be handled separately.
Its one-row rectangle keeps only its two ends. A 2 x 2 rectangle is unchanged.

## Revision 1

Use four-connected components of each foreground color, determine their
bounding boxes, and keep the distinct corner positions. This also handles
one-row and one-column rectangles without duplicate corner assumptions.
The public checker is the visible-example and execution test. No deliberately
wrong revisions were constructed. Query answers remain withheld.

## Scope

The observed background is zero and the observed components are solid
rectangles. Behavior for touching same-color rectangles or nonrectangular
components is not established by these visible examples.
