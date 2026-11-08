# Solve work log

Earlier exposure before this episode: none. I did not inspect any generator,
canonical rule, private label, prior solution, or audit evidence.

## Observation and hypothesis

Each visible input contains two occurrences of each of two nonzero colors. For
each color, its two cells are aligned either horizontally or vertically. The
output preserves all cells and fills every zero cell between each pair with
that pair's color, including both endpoints. The grid dimensions do not change.

This accounts for all three examples: the horizontal and vertical segments are
independent, and segment lengths explain the output color counts exactly.

## Implementation and probes

I copied the grid, grouped nonzero coordinates by color, and for every color
with exactly two aligned endpoints filled the inclusive row or column interval.
Unsupported colors (not exactly two cells or not axis-aligned) are left alone,
because the visible examples do not establish another behavior.

Before implementation, a direct assertion against train example 0 failed at the
provided `NotImplementedError`, confirming the test exercised the missing solve.
After implementation I checked all visible training examples locally, then used
the official visible-only checker.

## Remaining uncertainty

The examples do not show crossing segments, more than two cells of one color,
or diagonal pairs. The test queries contain the same demonstrated structure, so
no extra precedence or diagonal rule is needed for them.
