# Solve notes

This is a human-readable work log reconstructed during the required exposed
post-repair solve. I had earlier rule exposure from reviewing the assigned
generator, so this is not a blind solve; during this solve phase I used only the
visible examples printed by `review.py solve prepare` and did not reopen the
generator, Racket rule, reference answers, or earlier solution explanations.

## Visible observations

- Every input has 12 rows while every demonstrated output has 3 rows with the
  same width. That suggests four vertically stacked, aligned 3-row panels.
- Each panel is monochrome apart from zero background, but the panel colours can
  change roles across examples, so numeric colour order is not the operation.
- At each output coordinate, the value is selected independently from the four
  aligned input cells. A nonzero in the first (top) panel always wins.
- Where the first panel is zero, the second panel wins over lower panels.
- The remaining visible conflicts show the fourth panel wins over the third.
  Thus the inferred physical-panel priority is first, second, fourth, third.
- If all four aligned cells are zero, the output remains zero.

## Implementation

Split conceptually into four 3-row panels and, at each `(row, column)`, scan
panel indices `(0, 1, 3, 2)`, copying the first nonzero value. The code validates
that the input is a rectangular 12-row grid and returns a `3 × width` grid.
