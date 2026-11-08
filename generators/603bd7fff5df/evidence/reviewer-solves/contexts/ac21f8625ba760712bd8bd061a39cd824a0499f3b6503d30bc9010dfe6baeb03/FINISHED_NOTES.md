# Visible-only solve notes

The three demonstrations all use gray (`5`) cells as the stable geometric
markers.  In each example, the output width is the inclusive span between the
leftmost and rightmost gray columns.  The output height is the inclusive span
between the topmost and bottommost gray rows, extended by exactly one input row
above and one input row below.  All cells in that rectangle are copied without
recoloring; blue (`8`) cells outside it are distractors.

Hypothesis: find the bounding box of all gray cells, keep its column bounds, and
crop rows `[top_gray - 1, bottom_gray + 1]` inclusive.  This explains all output
shapes and every copied cell in the three visible examples.  I implemented that
rule directly, with explicit checks for missing gray cells and absent vertical
margin.  I did not consult a reference rule during this solve.  I had already
seen the generator/rule semantics during the repair phase, so this is an exposed
post-repair record rather than a blind solve.
