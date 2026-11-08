# Solve work log

I had no earlier exposure to this task's generator, Racket rule, private labels,
or prior solution notes. I used only the visible examples in `challenge.json`.

## Revision 1 — corner marker controls quarter-turn normalization

Observation: removing the lone gray `9` leaves one colored object. Its tight
bounding box is exactly the output up to rotation. The four training examples
place the `9` at top-left, top-right, bottom-right, and bottom-left respectively.
The corresponding outputs are the cropped object rotated 0, 1, 2, and 3
clockwise quarter-turns. This is consistent across rectangular and square-ish
objects and preserves background holes inside the crop.

Implementation: locate the `9`, crop the bounding box of all nonzero/non-9
cells, then rotate according to that corner. I added a visible-example pytest
first; it failed on the original `NotImplementedError`, then passed after this
implementation.

Remaining uncertainty: the visible data only shows the marker in exact grid
corners and one foreground object. The solution intentionally follows that
specific contract rather than guessing behavior for arbitrary marker positions.
