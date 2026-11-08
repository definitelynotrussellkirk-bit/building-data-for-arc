# Solve work log

Earlier exposure before this blind solve: **no**. I read only the packet-level
instructions and the public `solve-blind` presentation. I did not inspect either
task's generator, canonical rule, private labels, prior solutions, or audit records.

## Observations and hypotheses

The input contains a solid gray (`5`) rectangle and two nonzero singleton color
markers outside it. The output keeps the background and markers unchanged and
recolors every gray cell with one of the marker colors.

My first hypothesis was ordinary Manhattan distance from each marker. It explains
most cells but not the ties: in train 0, `(3, 3)` is equally far from colors 2 and
8 by raw Manhattan distance yet becomes 2, while the marker gaps differ. I then
projected each marker to its closest cell in the rectangle (clamp its row and
column to the rectangle bounds) and measured Manhattan distance *inside the
rectangle* from those projected entry cells. This exactly reproduces all three
visible outputs. Equal projected distances are resolved by the first marker in
row-major order, which is supported by train 2's two staircase-boundary ties.

I also rejected Euclidean distance. In train 2, rectangle cell `(3, 3)` is nearer
to the lower-right projected marker in Euclidean distance but is colored 7; the
Manhattan distances tie and row-major tie-breaking gives 7 as observed.

## Test discipline

I added `test_visible.py`, which reads only `challenge.json`'s public training
pairs. Before implementation it failed at the scaffold's `NotImplementedError`.
The implementation then passed all three public pairs. Remaining uncertainty is
whether the hidden generator ever emits more than two markers, a non-rectangular
gray component, or a different tie convention; none appears in the visible task.
