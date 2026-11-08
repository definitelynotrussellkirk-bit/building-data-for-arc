# Solve notes — 1034300a135f

This is an exposed post-repair solve. I had seen the task rule earlier while reviewing the generator, but during this solve phase I used only the visible examples and did not consult the generator, Racket source, reference solution, or hidden labels.

## Visible pattern

All examples preserve the input dimensions. One nonzero color overwhelmingly fills the input, so I treat it as the canvas/background. Every exceptional cell is a marker; zero must remain a marker because it becomes a visible output ring in all three examples.

The output is a set of concentric rings. The ring colors are determined by marker proximity to the input boundary:

1. Scan marker cells in row-major order.
2. For each marker, compute its minimum distance to any edge.
3. Stable-sort markers by that distance, nearest first.
4. Paint output ring 0, ring 1, and so on with the resulting marker colors.
5. If there are more geometric rings than markers, leave the deeper rings in the original background color.

## Discriminating observations

- Train 0 has marker distances `0, 3, 2, 4, 2` in row-major order. Its output ring sequence is `2, 2, 0, 4, 7`, so raw distance cannot be used directly as the ring index; markers are ranked after sorting.
- Train 2 has two distance-2 markers, colors 9 then 0 in row-major order. The corresponding consecutive rings are 9 then 0, supporting stable row-major tie order rather than reverse tie order.
- Train 0 has five markers on an 11×11 grid, leaving the center as background 6. Thus the last marker color is not extended indefinitely to the center.
- Zero is retained in the ordered sequence rather than ignored.

## Query expectations

- Query 0 marker order is `5(d0), 8(d1), 9(d2), 2(d3)`, filling all four rings of the 7×7 grid.
- Query 1 marker order is `2(d0), 2(d2), 0(d2), 8(d3), 6(d4), 1(d5)`; the distance-2 tie follows row-major order. The seventh/center ring remains background 5.

I implemented this directly in `solution.py` with a stable sort.
