# Post-repair visible-only solve notes

## Observation

All visible inputs are 4×4 and contain exactly one red cell (`2`) amid magenta (`6`) and several other colors. Each output contains only four red cells and twelve magenta cells. The other input colors disappear.

- Example 0 has its red cell in the top-right 2×2 quadrant; that entire quadrant becomes red.
- Example 1 has its red cell in the bottom-left quadrant; that quadrant becomes red.
- Example 2 has its red cell in the bottom-right quadrant; that quadrant becomes red.

## Hypothesis

Find the unique red cell, divide the grid at its row/column midpoints, fill the containing quadrant with red, and fill every other output cell with magenta. Decoration colors are irrelevant.

## Query predictions

Query 0 has red at `(0,0)`, so the top-left 2×2 quadrant should be red. Query 1 has red at `(0,3)`, so the top-right 2×2 quadrant should be red.

The implementation uses grid dimensions rather than hard-coding output arrays, although the visible task is 4×4. No generator, Racket rule, reference solution, private label, or earlier solution explanation was consulted during this solve episode. I had already seen the task rule while repairing the generator, so this is explicitly an exposed post-repair solve rather than a blind solve.
