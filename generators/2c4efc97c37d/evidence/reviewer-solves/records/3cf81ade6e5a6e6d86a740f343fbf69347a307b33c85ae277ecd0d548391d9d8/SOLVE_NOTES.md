# Post-repair visible-only solve notes

This is an exposed solve: I had already studied the selected task while repairing
its generator, but during this solve phase I used only the prepared visible
examples and did not reopen the generator, Racket rule, reference solutions, or
private labels.

## Hypothesis

The input contains several separated nonzero 4-connected components.  Read them
from left to right.  For each component, repeatedly remove every cell that has a
missing cardinal neighbor; the reported number is the last nonempty peel layer.
Return those depths as one horizontal row.

Evidence from the visible examples:

- Train 1 has a thin left component, a thick center component, and a thin right
  component, matching `[1, 3, 1]`.
- Train 2 is especially diagnostic: its left irregular object spans a 9x9
  bounding box, which would suggest 5 under a bounding-box shortcut, but the
  label is 4.  Actual cardinal peeling gives 4.  The single middle cell gives 1
  and the right 3x3 square gives 2, matching `[4, 1, 2]`.
- Colors appear to identify objects visually but do not determine the numbers.

## Implementation

`solution.py` finds binary nonzero components, sorts by minimum column then
minimum row, and computes exact cardinal onion depth with set erosion.  This
handles the irregular shapes shown in the demonstrations rather than assuming
rectangles or using bounding boxes.
