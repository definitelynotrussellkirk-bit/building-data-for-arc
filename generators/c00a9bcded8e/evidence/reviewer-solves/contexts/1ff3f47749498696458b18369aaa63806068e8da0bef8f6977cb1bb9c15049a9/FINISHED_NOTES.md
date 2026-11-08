# Solve notes

The three visible lessons contain dense, irregular two-color texture plus solid
single-color rectangles.  Components that are both large (at least 3×3 area)
and exactly fill their bounding boxes correspond one-for-one with output cells.
Their colors are read left-to-right within each spatial rectangle row, and the
rectangle rows are read top-to-bottom.  The output has three columns and as many
rows as there are vertical groups of rectangles.

I implemented an independent 4-connected component scan, retained solid
rectangular components of area at least nine, grouped their vertical centers
with a gap of four or more starting a new row, then sorted each row by horizontal
center.  This also rejects the visible irregular noise component of size 14 in
the second test input.  No reference implementation or private label was read
while producing this solution.  Earlier exposure to the task rule occurred
before this solve during the assigned generator review, so this is an exposed
solve rather than a blind one.
