# Solve work log

## Exposure statement

Before this solve I had not opened this task's generator, canonical rule,
reference solutions, private query labels, notes, or audit evidence. I used only
the public examples printed by `python3 review.py blind prepare` and the files in
`WORK/solve-blind/`.

## Revision 1 — component bounding-box corners

In every training example, each nonzero 4-connected object is replaced by the
four corners of its axis-aligned bounding rectangle, in the object's original
color, on an otherwise zero grid of the same shape. This explains both separate
objects of the same color in train example 1: they must be segmented as
4-connected components rather than grouped only by color. It also explains the
long color-2 object in train example 2, whose output contains only the four
corners of its 6-by-2 bounding box.

I implemented a color-preserving 4-neighbor flood fill, computed each component's
minimum and maximum row and column, and wrote the four corner cells. A set is
used for the corners so degenerate one-row or one-column boxes remain valid.
The main remaining uncertainty is whether diagonal contact should merge objects;
the visible examples support standard 4-connectivity, and no diagonal-only
contact case is shown.
