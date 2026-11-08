# Post-repair visible-only solve notes

## Visible evidence

- Training example 1 has a color-2 center at `(3,1)` and color-3 cells at
  `(2,1)` and `(4,1)`. The output is the 2×3 rectangle where the 3×3 square
  around the **first** color-3 cell overlaps the 3×3 square around the color-2
  cell. The later color-3 cell cannot be contributing, because including it
  would paint additional cells on rows 3–4.
- Training example 2 has one center of each color separated vertically by two;
  the output is the one-row overlap of their radius-1 square neighborhoods.
- Training example 3 again has a later color-3 distractor. The output is the
  2×2 overlap determined by the row-major first color-3 cell and the color-2
  cell.

## Hypothesis

Take the first `2` and first `3` in row-major order. Grow each into its clipped
Chebyshev-radius-1 (3×3) neighborhood. Return a same-size zero grid with color
`8` exactly on the set intersection. Ignore later cells of either seed color.

## Implementation

Use row-major scans for the selected centers, construct the two bounded cell
sets, intersect them, and paint the result. This directly handles horizontal,
vertical, and diagonal offsets and grid edges without shape-specific cases.

## Exposure declaration

This is a visible-example reconstruction, but I had earlier exposure to the
rule while repairing the assigned generator. I did not consult the generator,
Racket source, reference solution, or private labels during this solve phase.
