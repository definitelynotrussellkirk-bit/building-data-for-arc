# Blind solve notes

## Hypothesis

The output discards all spatial positions and packs the nonzero cells into one
row. Output width equals the number of nonzero input cells; cell colors are
retained in row-major order.

Evidence:
- Example 0 has three color-8 cells and returns three 8s.
- Example 1 has three color-3 cells and returns three 3s despite diagonal positions.
- Example 2 has nine color-1 cells and returns nine 1s.

This predicts query 0 as one 7 and query 1 as fourteen 5s. The examples contain
only one foreground color each, so behavior for mixed foreground colors is not
identified; preserving row-major values is the least-assumptive extension.
