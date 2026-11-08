# Solve work log

## Exposure statement

Before this solve I had not opened the task's generator, Racket rule, reference
solutions, private labels, audit records, or any generator assigned by this
packet. I used only the visible examples printed by `review.py blind prepare`.

## Hypothesis

Every changed region is a 2x2 window. When two equal nonzero cells occupy one
diagonal and the other two corners are background zero, the output fills those
empty corners with the same color, completing a monochrome 2x2 block. Existing
horizontal or vertical pairs remain unchanged. A diagonal pair is deliberately
left alone when either missing corner is occupied by another color; train 0 has
such a blocked 7 diagonal next to the 3 pair, and query 0 has a blocked 9
diagonal next to color 2.

I treat all qualifying windows simultaneously from the original input so a
newly completed block cannot create a cascade. The implementation preserves the
shape and all pre-existing cells.

## Probe and implementation

I wrote a visible-example regression harness outside the packet. Against the
initial template it failed with `NotImplementedError`, confirming the harness
exercised `solve`. I then implemented an exhaustive scan of all 2x2 windows,
collecting updates before applying them. Remaining uncertainty is only how a
hidden instance would resolve two overlapping qualifying windows that request
different colors for the same empty cell; no visible example contains that
case, and the stated rule's clean-background condition appears designed to
avoid it.
