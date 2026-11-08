# Solve work log

## Prior exposure

I had already inspected the assigned generator and canonical rule while repairing it, so this is an exposed post-repair solve, not a blind solve. During this solve I did not reopen the generator, Racket source, reference outputs, private query labels, or earlier solution explanations. I used only the visible presentation produced by `review.py solve prepare`.

## Revision 1 — seeded-frame activation

Visible pattern: each color-1 connected component is a rectangular outline. Empty rectangles remain unchanged. A rectangle with one or two color-2 cells strictly inside has every remaining interior zero changed to color 3; the color-2 cells and border remain unchanged. Train 0 and train 2 establish the one-seed case, while train 1 visibly establishes that two seeds still activate the frame. Multiple frames are handled independently.

Implementation: find four-connected color-1 components, take each component's bounding rectangle, detect any interior color 2, and fill only interior zeros with 3. This avoids a shortcut based on a fixed number, location, or shape of frames. Remaining uncertainty is limited to malformed/non-rectangular color-1 components, which the visible task does not present.
