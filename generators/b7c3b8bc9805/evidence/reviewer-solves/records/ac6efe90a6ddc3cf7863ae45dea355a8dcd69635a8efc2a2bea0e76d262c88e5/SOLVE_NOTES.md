# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, reference solution, private
labels, prior solve notes, or audit records.  I used only `challenge.json` and my
own calculations.

## Revision 1 — nearest marker selects the main diagonal

The gray color 5 forms one hollow rectangle.  Every output preserves the input
and fills only that rectangle's interior.  The interior is split at ceiling
half-height and ceiling half-width into four blocks.  The same color occupies
top-left and bottom-right; the other occupies top-right and bottom-left.

I compared the two non-gray colored pixels with the frame.  In examples 2–4,
the color in the top-left/bottom-right blocks is exactly the marker with the
smaller squared Euclidean distance to any gray frame cell.  Example 1 is an
exact distance tie; row-major order selects color 6, matching its output.  This
also explains the otherwise irregular marker placements better than guesses
based only on above/below or left/right orientation.

Implemented `solve(grid)` to locate the gray frame, select the nearer marker
with stable row-major tie-breaking, and fill the four ceiling-split blocks.
Remaining uncertainty: the examples do not distinguish distance to the frame
from several closely related distance-to-box metrics except on the observed
placements, and only one tie is shown.
