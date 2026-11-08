# Solve notes

## Hypothesis from the visible examples

The input contains one solid gray (`5`) rectangle and two singleton colored markers.  The output preserves the background and both markers, while replacing every gray cell with the color of its closest marker under Manhattan distance.

The visible examples also expose the tie rule.  In train example 0, rectangle cell `(1,3)` is distance 3 from both color 2 at `(0,1)` and color 8 at `(2,5)`, and it becomes 2.  In train example 1, rectangle cell `(5,4)` is distance 3 from both color 4 at `(5,1)` and color 1 at `(6,6)`, and it becomes 1.  Thus equal-distance cells choose the numerically lower marker color.  Row and column are retained as deterministic tertiary keys, though the two marker colors are distinct in every visible example.

## Implementation

Copy the grid.  Collect the two cells whose values are neither 0 nor 5.  For each gray cell, minimize `(Manhattan distance, marker color, marker row, marker column)` and write that marker's color.  Leave every other cell unchanged.

## Query expectations checked by hand

- Query 0: the two markers touch opposite lower sides of a 2×3 gray block, so the output should split the block by Manhattan proximity; any equal-distance cell chooses 4 over 8.
- Query 1: the color-6 marker is above the block and color 1 is upper-right.  The same distance comparison applies; ties choose 1.

No reference implementation or private query labels were consulted during this solve episode.  I had earlier rule exposure from the required generator-review phase, so this is an exposed solve, not a blind solve.
