# Solve work log

This is a human-authored work log. Earlier rule exposure is **yes**: before this
fresh episode was prepared, I had already reviewed this task's generator and
canonical behavior as part of the repair. During the solve episode I did not
reopen the generator, Racket rule, reference solutions, prior solve notes, or
private query labels.

## Revision 1 — finite graph-distance bisector

The visible examples contain unique red (2) and green (3) cells, open background
(0), optional gray walls (5), and newly painted cyan cells (8). In the wall-free
example, cyan is the full vertical Manhattan bisector between the seeds. In the
wall examples, the cyan locus bends around gaps, indicating shortest-path rather
than straight-line distance. The closed 3x3 ring in train example 2 leaves its
center unchanged, which distinguishes finite equal distances from two missing
distances.

Hypothesis: treat 5 as impassable, run separate four-neighbor BFS searches from
2 and 3 through every non-5 cell, and paint an original 0 cyan exactly when both
BFS distances exist and are equal. Preserve seeds, walls, non-ties, and cells
unreachable from either seed.

I implemented that rule directly. Remaining uncertainty before checking was only
whether some other nonzero color could be traversable; no such color appears in
the visible episode, and the transformation preserves 2/3 while using 5 as the
only obstacle.
