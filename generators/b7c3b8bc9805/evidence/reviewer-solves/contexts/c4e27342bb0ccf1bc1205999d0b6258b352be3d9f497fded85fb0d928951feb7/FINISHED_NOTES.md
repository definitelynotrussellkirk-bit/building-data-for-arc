# Solve work log

## Prior exposure

I had already inspected this task's generator and canonical rule while performing the assigned repair, so this is an **exposed** post-repair solve. During this solve phase I used only the visible examples in `challenge.json`/`README.md` and did not reopen the generator, Racket source, reference solutions, private labels, or earlier solution explanations.

## Revision 1

Hypothesis from the visible pairs: color 5 forms a rectangular frame. The only other two colors are singleton markers outside that frame. Read those markers in row-major order. Divide the frame interior into four quadrants, assigning the extra row/column of an odd-sized interior to the upper/left half. The first marker's location relative to the frame determines a diagonal parity class (UL/LR versus UR/LL). Fill matching-parity interior quadrants with the first marker's color and the other quadrants with the second marker's color; preserve the frame, markers, background, and shape.

Checks against the examples:

- Example 0: the first marker is upper-left, so its color occupies UL and LR.
- Example 1: both markers are above-right of the frame; the row-major first marker's color occupies UR and LL, matching the output despite the two markers sharing a corner region.
- Example 2: the first marker is lower-left, so its color occupies UR and LL.
- Example 3: the row-major first marker is lower-right and has the numerically larger color, so color magnitude is not the role; its color occupies UL and LR.

The implementation finds the gray bounding box and the two markers, computes the first marker's parity relative to the frame center, then fills the interior by quadrant parity. Remaining uncertainty is limited to malformed inputs outside the demonstrated domain; the function rejects those loudly rather than guessing.
