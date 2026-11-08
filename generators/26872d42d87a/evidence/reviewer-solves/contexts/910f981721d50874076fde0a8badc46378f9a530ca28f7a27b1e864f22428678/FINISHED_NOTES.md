# Visible-only solve notes

## Observations

- All three training outputs keep the input dimensions and preserve every existing nonzero cell.
- Every changed cell is a black `0` with immediate horizontal color-6 neighbours.
- Alternating fragments such as `6,0,6,0,6` therefore become solid runs.
- Wider same-row gaps are deliberate negatives: train 0 row 6 has 6s at columns 4 and 7 and remains unchanged between them; train 1 row 4 has 6s at columns 5 and 9 and remains unchanged; train 2 row 1 has 6s at columns 2 and 6 and remains unchanged.
- Vertical `6,0,6` arrangements at a border also remain unchanged, so orientation matters.
- Color 5 is decoration and remains unchanged.

## Hypothesis

Copy the grid, then change a cell from 0 to 6 exactly when its immediate left and right input neighbours are both 6. Evaluate the predicate from the original input so newly filled cells do not propagate.

## Query expectations

- Query 0: fill row 2 columns 2 and 4; row 3 column 3; row 4 columns 4 and 6. Preserve row 1's wider span and the vertical border pattern in rows 6–8.
- Query 1: fill row 3 column 7; rows 6 and 8 columns 2 and 4. Preserve row 4's wider span and the right-border vertical pattern.
