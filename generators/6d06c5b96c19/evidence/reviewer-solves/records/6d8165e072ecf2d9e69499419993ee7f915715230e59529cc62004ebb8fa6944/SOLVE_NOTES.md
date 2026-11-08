# Blind solve notes — 6d06c5b96c19

## Observation

Each input has one extra leftmost column. Exactly one cell in that column is
color `2`. The visible outputs have the same row count and one fewer column.

- In training examples 1 and 2, the marker is at row 0. Removing the first
  column exactly produces the output.
- In training example 3, the marker is at row 1. Removing the first column and
  cyclically shifting the payload rows downward by one exactly produces the
  output (the final payload row wraps to the top).

## Hypothesis

The left column is a control strip. Remove it, then rotate the remaining rows
**down** by the marker row index. The marker color itself is always `2` in the
visible examples.

## Implementation

`solution.py` validates that there is exactly one `2` in the leftmost column,
removes that column, and applies the cyclic shift. No reference source, private
labels, generator, or prior explanation was consulted.
