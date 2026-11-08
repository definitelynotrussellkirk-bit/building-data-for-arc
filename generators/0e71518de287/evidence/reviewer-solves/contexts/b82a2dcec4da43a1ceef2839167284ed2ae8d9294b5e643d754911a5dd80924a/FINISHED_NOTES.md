# Solve work log

I had not opened this task's generator, rule, reference solution, private labels,
or audit evidence. I used only the visible examples produced by `blind prepare`.

## Revision 1 — indicated hollow frame

**Hypothesis.** Every input has two hollow rectangular frames drawn in color 4
and one nonzero, non-4 marker. The marker is orthogonally adjacent to exactly one
frame. The output preserves the input and fills that frame's zero-valued interior
with the marker color.

**Visible evidence.** In the four demonstrations the marker appears respectively
to the right, above, below, and left of the changed frame. The number of newly
colored cells equals that frame's interior area: 1, 2, 2, and 2. The other hollow
frame is unchanged.

**Implementation/probe.** Find 4-connected components of color 4, choose the
component with minimum Manhattan distance to the marker, take its bounding box,
and recolor zero cells strictly inside the box. This also predicts query 0 fills
the two interior cells of the left 4x3 frame with color 2, while query 1 fills the
four interior cells of the upper-right 4x4 frame with color 8.

**Alternatives considered.** Filling the largest or nearest-by-center frame does
not explain all examples; direct adjacency does. Remaining uncertainty is limited
to unseen malformed/non-rectangular frames, which the visible task does not show.
