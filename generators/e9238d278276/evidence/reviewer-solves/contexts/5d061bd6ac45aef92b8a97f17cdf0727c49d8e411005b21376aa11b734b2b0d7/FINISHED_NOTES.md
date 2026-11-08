# Blind solve notes — e9238d278276

## Visible pattern

Across all four training pairs, each column is transformed independently. The
nonzero entries in a column are moved to the topmost rows while retaining their
original top-to-bottom order; every remaining cell becomes zero.

Examples checked mentally:

- In training pair 1, column 0 has `8, 2` from top to bottom and becomes `8, 2`
  in output rows 0 and 1.
- In training pair 2, column 2 has `1, 9, 7` and becomes output rows 0–2 in that
  same order.
- Horizontal positions and colors never change.

## Hypothesis

Apply upward gravity separately to every column, treating zero as empty space.
This predicts a deterministic output for all visible examples and both queries.

## Implementation

Build an all-zero grid of the same dimensions. For each column, collect all
nonzero values in row order and write them from output row 0 downward.
