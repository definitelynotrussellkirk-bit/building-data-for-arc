# Solve work log

Earlier exposure: none. I did not inspect this task's generator, Racket rule,
reference solution, private labels, prior notes, or the assigned repair generator.

## Revision 1 — extend each two-cell bar at both ends

All three visible examples contain two differently colored, axis-aligned bars of
length two. Each output extends a bar by one cell beyond each endpoint. Extensions
outside the grid are clipped: this explains why an interior bar grows from length
2 to length 4, while a bar touching an edge grows only to length 3.

I implemented the rule independently for each nonzero color. The program locates
the two cells, confirms they are orthogonally adjacent, derives the unit direction,
and paints one cell before the first endpoint and one after the second when those
coordinates remain inside the grid.

Remaining uncertainty: the visible examples do not show overlapping extensions or
colors split into more than one object. I leave unexpected colors unchanged rather
than invent behavior outside the demonstrated domain.
