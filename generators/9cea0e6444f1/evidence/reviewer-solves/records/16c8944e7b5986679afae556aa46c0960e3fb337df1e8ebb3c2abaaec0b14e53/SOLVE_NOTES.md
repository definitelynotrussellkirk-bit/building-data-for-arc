# Solve work log

## Prior exposure

Before this solve phase I had already inspected and repaired the assigned generator, so I had earlier exposure to the intended transformation. I did not consult the Racket authority, generator implementation, private labels, or earlier solution text while writing or checking this solve. I used only `WORK/solve/challenge.json` during this phase.

## Visible-example hypothesis

Each input contains a shape in color 1 and another in color 2, sometimes plus isolated color-7 distractors. For each of colors 1 and 2 independently, translate its occupied cells so that its own minimum row and minimum column become `(0, 0)`. Overlay the two normalized shapes, crop to their union, and paint every union cell green (`3`); all other output cells are `0`. Color 7 is irrelevant.

This accounts for all three demonstrations, including the example with two color-7 cells and examples where the two source shapes begin at different absolute positions and have different extents. Competing readings based on the absolute union, intersection only, one source color only, or all nonzero colors disagree with at least one visible pair.

## Implementation

`solution.py` collects and independently normalizes colors 1 and 2, takes their set union, sizes the result to the union's bounding dimensions, and paints the union green. No query labels are available, so correctness beyond the visible examples remains unknown.
