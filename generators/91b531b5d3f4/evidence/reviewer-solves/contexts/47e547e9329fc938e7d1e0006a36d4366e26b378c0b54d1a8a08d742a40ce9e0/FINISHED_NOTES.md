# Blind solve notes

## Attempt 1 — column headers recolor marker cells

Observed pattern across all four demonstrations:

- The first row contains one or more nonzero colored cells that act as column headers.
- Only cells with value `1` are markers eligible for replacement.
- A marker in a column whose first-row cell is nonzero takes that header color.
- Markers in columns with a zero header remain `1`.
- Existing non-`1` colored cells remain unchanged, even when they share a header column.

This explains the unchanged `8` below header `4` in training example 3 and the unchanged
`5` below header `7` in training example 4, ruling out blanket column recoloring.
Implementation applies the rule independently to every cell using the first row as the
lookup table.
