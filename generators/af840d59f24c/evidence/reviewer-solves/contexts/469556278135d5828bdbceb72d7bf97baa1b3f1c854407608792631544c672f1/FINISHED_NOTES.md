# Solve work log

I had not seen task `af840d59f24c`, its rule, generator, private labels, or an earlier solution before this visible-only solve.

## Observation and hypothesis

Across all four training examples, every input zero is recolored while every nonzero cell is unchanged. The replacement color depends only on the zero's column: collect the columns that contain at least one zero, order those columns from left to right, and assign colors `1, 2, ...` in that order. Every zero in the same column receives the same color.

Checks against the examples:

- Example 0 has zero-bearing columns `[1, 2, 7, 8]`, which become colors `[1, 2, 3, 4]`.
- Example 1 has eight zero-bearing columns `[0, 1, 6, 7, 9, 10, 12, 14]`, matching output colors `1` through `8`.
- Example 2 retains all pre-existing color-9 cells and maps zero-bearing columns `[2, 3, 9, 10, 13, 14]` to colors `1` through `6`.
- Example 3 maps columns `[1, 2, 8, 9, 12]` to colors `1` through `5`.

I considered component size or top-to-bottom ordering, but those do not explain why disconnected zeros in one column share a color or why colors increase exactly with column position. The implementation therefore copies the grid and replaces only zeros using the left-to-right zero-column rank.

## Query prediction

- Query 0 has zero-bearing columns `[1, 2, 3, 8]`, so they receive colors `1, 2, 3, 4`.
- Query 1 has zero-bearing columns `[3, 4, 5, 7, 10, 11]`, so they receive colors `1, 2, 3, 4, 5, 6`.

Remaining uncertainty is low: the visible data are fully consistent, although private query labels are intentionally unavailable.
