# Solve work log

## Prior exposure

I had not opened this task's generator, Racket rule, notes, solutions, audit records,
or private query labels. I used only the visible challenge produced by `blind prepare`.

## Revision 1 — geodesic Voronoi regions

The two singleton colors are sources: color 2 owns output color 8 and color 3 owns
output color 4. Empty cells tied between the sources stay color 0, while color 5 is
preserved as a wall.

A plain Manhattan-distance interpretation explains train example 0, but train
example 1 provides a decisive probe against it. At `(5, 6)`, direct Manhattan
measurements favor the color-3 source, yet the expected cell is 0. Treating the
row-4 color-5 cells as impassable makes the shortest four-neighbour paths from the
two sources both length 5, exactly explaining the tie. The vertical color-5 wall in
example 2 likewise bends and blocks the wavefronts.

I therefore implemented two breadth-first searches over non-5 cells, one from each
source. For each original 0: emit 8 when the color-2 distance is smaller, 4 when the
color-3 distance is smaller, and retain 0 on a tie (including mutual
unreachability). All original nonzero cells are preserved.

Before implementation I ran a visible-pair harness against the template and saw the
expected `NotImplementedError` (exit 1). The remaining uncertainty is whether some
unseen instance uses additional obstacle colors; all three visible examples use
only color 5 for this role, so the implementation follows that evidence rather than
generalizing without support.
