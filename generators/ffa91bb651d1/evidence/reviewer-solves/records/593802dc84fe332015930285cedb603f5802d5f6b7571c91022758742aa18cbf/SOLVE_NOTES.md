# Blind solve work log

## Visible evidence

The output has the same dimensions as the input in all three demonstrations.
Changes happen within individual rows; no column or cross-row relationship is
needed.

Candidate rule: find rows whose only nonzero cells are two equal-colored
endpoints, then fill the inclusive horizontal interval between them with that
color. Copy every other row unchanged.

Evidence supporting the restrictions:

- Train 0 fills the `4`, `6`, and `3` endpoint pairs. The row with colors `8`
  and `9` stays unchanged, and the row with three `4` cells stays unchanged.
- Train 1 fills the two-cell `4` and `5` rows. A row containing a `6` pair plus
  a `7` singleton stays unchanged; the three-cell `9` row also stays unchanged.
- Train 2 fills the two-cell `9`, `7`, and `8` rows. The mixed-color endpoint
  row and the three-cell `2` row stay unchanged.

This distinguishes the intended rule from the broader rival “fill between any
same-colored pair,” which would incorrectly modify rows containing additional
nonzero cells.

## Predicted query behavior

- Query 0: fill row 5 from columns 0 through 6 with color 4, and row 15 from
  columns 2 through 5 with color 9. Leave all other rows unchanged.
- Query 1: fill row 3 from columns 5 through 9 with color 7, row 5 from columns
  4 through 8 with color 5, and row 7 from columns 2 through 5 with color 4.

No generator, canonical rule, reference solution, private label, or prior solve
explanation was consulted. The initial untouched stub was executed once as a
`diagnostic_probe` to verify the visible-only checker before implementing this
rule.
