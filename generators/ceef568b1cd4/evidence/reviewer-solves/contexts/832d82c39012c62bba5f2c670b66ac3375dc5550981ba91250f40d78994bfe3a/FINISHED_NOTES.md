# Solve work log

## Exposure declaration before solving

I had not opened the generator, Racket rule, notes, reference solutions, private
labels, or audit material for task `ceef568b1cd4`. I used only the visible
examples printed by `python3 review.py blind prepare` and the public files under
`solve-blind/`.

## Revision 1 — component-area filter

Hypothesis: treat each same-color object as a **4-connected** component. Replace
with background every component whose area is a non-trivial power of two
(`2, 4, 8, ...`), while preserving singleton components and components of all
other sizes.

Evidence from the visible examples:

- Example 0 removes two area-4 components and keeps the area-1 component.
- Example 1 separates the color-6 cells into 4-connected components of areas 7
  and 8. The area-7 component stays and the area-8 component disappears. The
  area-10 component stays and the area-2 component disappears.
- Example 2 removes both area-2 components and keeps both area-1 components.
- Four-connectivity is required: in example 1, the area-7 and area-8 color-6
  components touch only diagonally. Eight-connectivity would incorrectly merge
  them into one area-15 object.

Predicted query behavior:

- Query 0 removes only the area-4 color-5 zigzag. The color-1 objects have areas
  9 and 6; the color-3 objects have areas 3 and 1, so they remain.
- Query 1 removes the area-2 color-7 domino and area-4 color-3 object, preserving
  the two singleton objects.

Implementation: iterative flood fill over four orthogonal neighbors, followed by
an integer power-of-two test. Remaining uncertainty is low; the training examples
strongly distinguish component area from whole-color counts and distinguish
4-connectivity from 8-connectivity.
