# Solve notes

## Visible evidence

- Example 1 has color-4 endpoints at `(7,1)` and `(7,7)` and outputs only color 8 at `(7,4)`, their midpoint.
- Example 2 has endpoints at `(3,8)` and `(3,10)` and outputs only color 8 at `(3,9)`. This is far from the canvas center, so “always mark the grid center” is directly refuted.
- Example 3 has diagonal endpoints at `(3,2)` and `(11,10)` and outputs only color 8 at `(7,6)`, again the coordinate-wise midpoint.

## Hypothesis

Find the two nonzero endpoint cells. Return an all-zero grid of the same shape with one color-8 cell at their exact coordinate-wise midpoint. Do not preserve the endpoints and do not paint the full segment.

## Implementation choices

The solver finds exactly two nonzero cells rather than assuming their input color. It rejects an instance without an integer midpoint instead of silently rounding. The visible examples support horizontal and diagonal cases; the coordinate-wise formula also covers a vertical segment.

## Revision 1

Implemented the midpoint rule directly. No reference source or private labels were consulted during this solve. I had earlier exposure to the task rule while reviewing the assigned generator, so this is an exposed post-repair solve rather than a blind solve.
