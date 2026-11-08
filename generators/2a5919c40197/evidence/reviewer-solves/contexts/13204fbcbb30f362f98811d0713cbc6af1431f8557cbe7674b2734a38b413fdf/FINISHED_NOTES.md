# Visible-only solve notes

## Observations

- Training example 1: the mixed row `[7,2,7]` becomes all `0`; each uniform
  row becomes all `5`.
- Training example 2: the only completely uniform row is the all-`7` row, and
  it alone becomes `5`; every other row contains at least two colors and becomes
  `0` across its full width.
- Training example 3 repeats the same distinction at width three: all-`9` and
  all-`7` rows become `5`, while `[1,6,1]` becomes `0`.

## Hypothesis

Classify rows independently using the entire row. If all cells in a row have the
same color, replace the whole row with `5`; otherwise replace the whole row with
`0`. The output preserves the input dimensions.

This also distinguishes the first test's long mixed rows from its all-`9` and
all-`2` rows, and classifies the second test's two `[8,8,3]` rows as mixed while
classifying `[6,6,6]` as uniform.
