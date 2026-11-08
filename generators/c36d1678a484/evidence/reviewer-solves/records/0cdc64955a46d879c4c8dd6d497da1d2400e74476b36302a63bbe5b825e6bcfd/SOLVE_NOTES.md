# Solve notes

This is a human work log based only on `solve/challenge.json` after the fresh episode was prepared.

## Observations

- Grid shape stays unchanged and rows appear independent.
- In every training example, a row containing exactly one nonzero cell of color 7 becomes a full row of 7s.
- Rows with two or more 7s remain unchanged.
- A singleton color 8 remains unchanged.
- A row containing one 7 together with an 8 remains unchanged.
- Blank rows remain unchanged.

## Hypothesis

For each row, collect its nonzero values. Replace the whole row by 7 exactly when that list is `[7]`; otherwise copy the row unchanged.

This directly distinguishes the visible alternatives “fill any row containing 7,” “fill any singleton,” and “fill any row with exactly one 7 even when another color is present.” No failed implementation revision was needed before the first check.
