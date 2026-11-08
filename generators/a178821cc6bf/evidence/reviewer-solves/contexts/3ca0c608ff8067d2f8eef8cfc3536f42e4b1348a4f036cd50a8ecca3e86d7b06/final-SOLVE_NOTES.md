# Solve notes

## Visible structure

All three demonstrations have eight input columns and four output columns with
the same number of rows. I split each input row into aligned left/right halves:
columns `0..3` and `4..7`.

## Hypotheses checked

1. **Copy zero locations from one panel.** Rejected. In train 1 row 0, left
   column 0 is zero but its aligned right cell is nonzero and the output is 0.
   Symmetric one-panel rules fail elsewhere.
2. **Mark equal raw values.** Rejected directly by the visible same-color
   example (train 2): aligned nonzero `9/9` pairs remain output 0.
3. **Mark aligned cells that are both zero.** This matches every output cell in
   all three visible demonstrations. Positive cells are exactly `0/0`; the
   `0/nonzero`, `nonzero/0`, and `nonzero/nonzero` cases are all 0.

## Implementation

For each row and each `c` in `0..3`, return `4` iff `grid[r][c] == 0` and
`grid[r][c+4] == 0`, else `0`. The solution validates the visible fixed width
rather than guessing a generalized split.
