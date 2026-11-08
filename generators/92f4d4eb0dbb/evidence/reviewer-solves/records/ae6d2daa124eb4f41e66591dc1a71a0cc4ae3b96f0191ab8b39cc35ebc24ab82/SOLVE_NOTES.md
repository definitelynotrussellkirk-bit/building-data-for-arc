# Solve notes

## Visible-example hypothesis

All examples preserve the canvas and every 0. They locate the first and last
rows containing color 1, use the arithmetic midpoint of those two row indices,
and recolor only color-1 cells on rows strictly below that midpoint to color 2.

Evidence from the visible examples:

- Example 1 occupies rows 3..8, midpoint 5.5; rows 6..8 change.
- Example 2 occupies rows 0..4, midpoint 2; row 2 stays 1 while rows 3..4 change.
  This distinguishes strict `row > midpoint` from an inclusive midpoint rule.
- Example 3 occupies rows 0..5, midpoint 2.5; rows 3..5 change.

The rule is independent of shape, column, and connectivity. I implemented the
comparison without floating point as `2 * row > min_row + max_row`. No earlier
failed revision was needed because the odd-height second example directly
settles the only obvious midpoint-boundary ambiguity.
