# a3fcfe29ef7e

A fixed-width `h x 7` input contains two aligned three-column panels separated by
one solid column.  Produce an `h x 3` output whose cell is color 3 exactly when
both aligned panel cells are zero; all other occupancy states output 0.

Generator v3.0.0 samples the four Boolean states directly, so every ordinary
input contains `00`, `10`, `01`, and `11`, with an exact `both_zero_count` of
1..6.  A two-step curriculum alternates different and equal panel foreground
colors; equal-color `11` cells refute the canonical-fitting shortcut “mark raw
equality.”  Height, left/right/separator colors, positive count, and six layout
signatures are exact observable controls.  Every fourth sample is a canonical-
profile anchor.  Strict validation accepts all six canonical inputs and rejects
out-of-grammar teaching fixtures.

Kind: `per_puzzle`. Current version: `3.0.0`. Canonical rule hash:
`f7f19079511e`.
