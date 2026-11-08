# Solve work log

## Prior exposure

Before this blind solve I read only packet-level instructions and general ARC design guidance. I did not open task `0b999a8ea028`'s generator, Racket rule, private labels, prior solutions, notes, or audit records. I had no task-specific rule exposure.

## Revision 1 — intact isolated frames receive the largest motif

The examples contain color-1 hollow rectangles plus one or more other colored objects. My hypothesis is:

1. Treat each 4-connected color-1 component as a candidate frame.
2. Accept it only when the component is exactly the border of one hollow rectangle. This rejects the broken lower-left frame in train 2 and the two touching frames in train 3, whose joined component is not one rectangle border.
3. Choose the largest 4-connected nonzero, non-1 object as the motif. This selects the color-9 diamond rather than the color-6 domino in train 1.
4. Erase everything, then place an unchanged copy of that motif in every accepted frame, centered in the frame interior. Integer centering uses the upper/left choice when a one-cell asymmetry is unavoidable, matching train 0.

I checked the geometry manually on all four visible examples. The 5×5 frames in train 0 have 3×3 interiors, so the 2×2 L motif starts one cell inside their upper-left borders. The 6×6 frame in train 2 has a 4×4 interior, so the 2×2 motif has a one-cell margin on all sides. The 7×7 frame in train 1 centers the 3×3 diamond inside its 5×5 interior.

A temporary visible-example regression script first failed on the untouched `NotImplementedError`, then was used to check the implementation. Remaining uncertainty: the visible data does not distinguish “largest motif” from some location-based selector, but largest-component selection explains the explicit smaller distractor in train 1 and query 1 without using hidden information.
