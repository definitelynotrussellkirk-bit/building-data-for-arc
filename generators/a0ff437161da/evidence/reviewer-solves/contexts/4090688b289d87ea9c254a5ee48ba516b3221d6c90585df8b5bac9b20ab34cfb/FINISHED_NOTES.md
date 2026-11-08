# Solve work log

## Disclosure

I had earlier exposure to the task family while repairing and testing its generator. During this post-repair solve I did not reopen the generator, canonical Racket rule, reference solutions, private labels, or earlier solution notes. I used only the visible challenge prepared in this directory.

## First and only revision

Each visible input is an 8-colored rectangle with one differently colored marker. The output preserves the shape and fills an axis-aligned rectangle in the marker's color, with the marker at one corner and a canvas corner at the opposite corner.

The selected canvas corner is the one with minimum Manhattan distance from the marker:

- Train 0 has marker `(6, 8)` in a `16 x 17` grid. Both upper corners are distance 14, and the output reaches the upper-left corner. This supplies a top-corner tie and selects upper-left.
- Train 1 has marker `(2, 4)` in a `6 x 6` grid. Upper-right is uniquely nearest (distance 3), matching the `3 x 2` filled rectangle.
- Train 2 has marker `(8, 7)` in an `11 x 15` grid. Both lower corners are distance 9, and the output reaches lower-left. This supplies a bottom-corner tie and selects lower-left.

Those examples support row-major corner priority for ties: upper-left, upper-right, lower-left, lower-right. Python's `min` over a tuple in that order implements the priority without a separate branch. The filled rectangle includes both the marker row/column and the chosen boundary row/column.

Predictions before checking:

- Query 0: `(3, 2)` in `6 x 8`; lower-left is uniquely nearest, so fill rows `3..5`, columns `0..2` with color 4.
- Query 1: `(7, 4)` in `15 x 11`; upper-left and lower-left tie at distance 11, so row-major priority chooses upper-left and fills rows `0..7`, columns `0..4` with color 9.

I stopped after the first checked revision because it exactly reproduced every visible training output. Private query correctness was not available and was not used.
