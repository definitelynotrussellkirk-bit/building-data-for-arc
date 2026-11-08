# Post-repair solve work log

This is a human work log based only on the visible episode printed by
`solve_episode.py prepare`. I had earlier rule exposure while repairing this
same generator, so this is **not** a blind solve; I did not reopen the generator,
Racket rule, reference solutions, private labels, or earlier solution text during
this solve phase.

## Hypothesis

Each 4-connected azure (`8`) object is handled independently in the coordinate
frame of its own bounding box. The output preserves the canvas and preserves any
missing cell/notch inside that box. Only occupied `8` cells are recolored.

The outer two-cell frame is split into four corner regions:

- top-left: `6`
- top-right: `1`
- bottom-left: `2`
- bottom-right: `3`

Cells that are at least two rows from the top/bottom and two columns from the
left/right are `4`. Along the left/right side strips, the upper half uses the top
corner color and the lower half the bottom corner color. Along the top/bottom
strips, the left half uses the left corner color and the right half the right
corner color. Odd dimensions give the central row/column to the upper/left half,
matching the 7×9 visible object. Background holes stay `0` rather than being
filled.

## Implementation

Revision 1 finds 4-connected `8` components, computes each component bounding
box, and applies the five-region coloring only to the component's occupied cells.
No diagnostic or deliberately wrong revision was needed because all three visible
training examples, including interior holes and edge notches, distinguish the
cell-preserving rule clearly.
