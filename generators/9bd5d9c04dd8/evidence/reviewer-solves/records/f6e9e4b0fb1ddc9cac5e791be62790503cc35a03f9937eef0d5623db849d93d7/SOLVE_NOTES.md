# Blind solve notes — 9bd5d9c04dd8

## Visible observations

- Every visible input contains three separated, completely filled 3×3 nonzero tiles on a zero background.
- The output is exactly one of those tiles, with no recoloring or geometric transform.
- Across the three training examples, the selected tile is uniquely the one containing the greatest number of cells colored `1`:
  - example 0: selected tile has eight `1` cells;
  - example 1: selected tile has nine `1` cells;
  - example 2: selected tile has two `1` cells, versus one and zero in the others.

## Hypothesis

Extract each 4-connected non-background component, crop it to its bounding box, and return the 3×3 component with the largest count of color `1`.

## Query predictions

- Query 0: the three tiles contain 2, 4, and 5 cells of color `1`; return the lower-left tile.
- Query 1: the three tiles contain 4, 0, and 5 cells of color `1`; return the lower-left tile.

## Implementation notes

The solver infers the background as the most frequent color, extracts 4-connected non-background components, prefers complete 3×3 candidates, and ranks them by their number of `1` cells. No generator, rule, answer, notes, audit evidence, or prior solution was consulted.
