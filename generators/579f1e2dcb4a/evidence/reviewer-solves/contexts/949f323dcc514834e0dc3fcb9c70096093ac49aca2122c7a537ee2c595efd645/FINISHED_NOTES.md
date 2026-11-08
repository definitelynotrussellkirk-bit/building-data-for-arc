# Solve work log

## Prior exposure

This is an **exposed post-repair solve**, not a blind solve. Before this episode I
had already read and tested the task's generator and canonical Racket rule while
repairing the source. During this solve episode I did not reopen the generator,
Racket rule, private labels, reference outputs, or earlier solution explanations;
I used only the visible examples printed by `solve_episode.py prepare` and this
local Python program.

## Revision 1 — crop 4-connected nonzero components, then pack by left edge

**Visible observations.** Each input contains several sparse nonzero objects on a
black background. Different colors can belong to one object when their cells are
orthogonally adjacent. In palette-6 examples, the same color can also form two
separate objects that touch only diagonally. Each output is much smaller, retains
the exact sparse pixels inside each object's tight bounding rectangle, and places
those rectangles side by side with one black separator column.

Across all three demonstrations, output order follows the objects' original left
edges rather than their top rows or colors. The first two demonstrations also show
a same-left pair: the upper component precedes the lower component, so the
secondary key is top row. Crops are top-aligned; the one-cell crop in the first
two examples remains on output row 0 rather than being bottom-aligned.

**Hypothesis.** Find nonzero components using 4-neighbor connectivity regardless
of color. Crop each to its tight bounding box, sort by `(original left,
original top)`, and paste the crops top-aligned with exactly one zero column
between them. Preserve internal zeros instead of filling bounding boxes.

**Alternatives rejected by visible evidence.** Same-color segmentation would
split multicolor objects; 8-connectivity would merge the diagonal same-color
pieces; sorting by top or color changes demonstrated order; solid rectangles,
bottom alignment, and zero-gap packing all disagree with the shown outputs.

No failed implementation preceded this revision; I did not manufacture one.
