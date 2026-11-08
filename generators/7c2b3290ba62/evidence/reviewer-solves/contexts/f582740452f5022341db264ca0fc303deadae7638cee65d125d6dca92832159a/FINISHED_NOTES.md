# Visible-only solve notes

## Hypothesis

The full color-9 columns partition each input into equal-size panels. The first
panel is a partial source shape, the second is the target shape, and the
remaining panels are candidates. Color identity within a panel varies, so I
compare occupied coordinates (all nonzero, non-9 cells), not numeric colors.

The output has one cell per candidate. A candidate pair is marked with 8 exactly
when the union of its occupied coordinates with the first panel equals the
second panel.

## Checks against the visible examples

- Example 0 has four candidates and marks candidates 0 and 3. Together with the
  one source cell, their singleton coordinates reconstruct the three target
  cells.
- Example 1 marks candidates 3 and 4; their occupied cells supply the target
  positions missing from the source while the other candidates add positions
  outside the target.
- Example 2 similarly marks candidates 2 and 4 among six candidates.

I implemented panel splitting from the full-height 9 columns, coordinate-set
union, and the first matching unordered pair. No Racket rule or private label
was consulted during this solve phase. I had earlier rule exposure while
repairing this same generator and will declare that honestly at finish.
