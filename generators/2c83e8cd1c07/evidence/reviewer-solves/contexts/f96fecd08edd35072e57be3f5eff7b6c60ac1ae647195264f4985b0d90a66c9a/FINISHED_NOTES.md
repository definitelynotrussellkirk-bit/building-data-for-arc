# Solve notes

This is a human visible-example work log. I had earlier rule exposure from reviewing the assigned generator, so this is not blind; I did not consult the generator, Racket source, reference solution, or private labels during this solve episode.

## Hypothesis

Each nonzero color appearing exactly twice defines a candidate line segment. If its two cells lie on a perfect 45-degree diagonal and every interior cell on that diagonal is zero in the **original input**, fill the segment inclusively with that color. If another nonzero cell blocks the interior, leave that pair unchanged. Evaluate all pairs from the original grid rather than allowing one newly painted segment to block another.

## Evidence from the visible demonstrations

- Demonstration 1: color 2 has a clear southeast diagonal and is completed; color 6 would pass through the color-2 endpoint and is not completed.
- Demonstration 2: colors 7 and 9 have clear parallel diagonals and are completed; color 3 crosses the existing color-7 endpoint and remains only at its endpoints.
- Demonstration 3: colors 6, 7, and 9 are clear and completed; color 1 is blocked by an existing 9 cell and remains unchanged.

## Test predictions

- Test 1: complete the 6 diagonal from `(2,5)` to `(5,8)`; do not complete the 4 diagonal because `(2,5)` blocks it.
- Test 2: complete the 6 diagonal from `(2,3)` to `(5,6)` and the 5 diagonal from `(3,3)` to `(6,6)`; do not complete the 8 diagonal because `(3,3)` blocks it.

The implementation groups original nonzero cells by color, requires exactly two cells and equal nonzero row/column displacement, tests original interior cells for zero, and writes qualifying paths into a copy.
