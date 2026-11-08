# Visible-only solve notes

## Exposure declaration

This is the required post-repair solve. I had already inspected and repaired the assigned generator before this episode, so earlier rule exposure is **yes**. During this solve phase I used only the public examples printed by `solve_episode.py prepare`; I did not reopen the generator, Racket authority, canonical solution, private labels, or previous solution explanations.

## Hypothesis 1

Every nonzero color occurs exactly twice. In each example the two cells of a color share either a row or a column. The output starts as an all-zero grid of the same shape and paints the inclusive straight segment between the two markers with that color.

Evidence from the visible examples:

- Train 0: color 5 joins vertically from rows 1 through 7 in column 0; colors 1 and 4 join horizontally.
- Train 1: colors 1 and 5 join horizontally, while color 6 joins vertically.
- Train 2: color 6 joins vertically, while colors 9 and 4 join horizontally.
- Endpoints are included, and unrelated zero cells remain zero.

## Implementation

Collect coordinates by nonzero color. For each color with exactly two coordinates, fill the inclusive row interval when the rows match, or the inclusive column interval when the columns match. Begin from a fresh zero grid rather than copying the input.

## Expected query behavior

- Query 0: horizontal segments for colors 7 and 2; a vertical segment for color 3.
- Query 1: a vertical segment for color 8; horizontal segments for colors 3 and 7.
