# Solve work log

## Prior exposure

Before this blind solve I had not opened task `0a54983176e5`'s generator,
canonical rule, notes, solutions, audit records, or private labels. I had only
read the packet-level instructions and the visible examples produced by
`solve_episode.py blind prepare`.

## Revision 1 — mirror across the color-8 axis

Hypothesis: all color-8 cells lie on one row or one column and mark a mirror
axis. Copy every other nonzero cell to its reflected, in-bounds location, but do
not overwrite an existing cell.

Evidence from the visible examples:

- Train 0: the 8s lie on row 3. Reflecting the two color-1 cells on row 1 adds
  `(5,1)` and `(5,8)`; reflecting the two color-6 cells on row 2 adds `(4,4)`
  and `(4,7)`. The remaining reflected pair is already occupied by different
  colors at `(0,5)` and `(6,5)`, so both existing cells stay unchanged.
- Train 1: the 8s lie on row 1. Only color 4 at `(2,6)` has an in-bounds empty
  reflection, producing `(0,6)`.
- Train 2: the 8s lie on column 7. Reflections add color 4 at `(1,8)` and color
  2 at `(6,8)`; all other reflected coordinates are out of bounds.

Predicted queries:

- Query 0: horizontal axis row 1; add color 2 at `(0,1)`. The cells at
  `(0,10)` and `(2,10)` reflect onto one another but contain different colors,
  so neither is overwritten.
- Query 1: vertical axis column 6; add color 4 at `(5,8)` and `(5,9)`.

Implementation keeps malformed inputs unchanged when the 8-cells do not form a
single horizontal or vertical axis. Remaining uncertainty: unseen inputs with a
single 8 marker would satisfy both axis tests; the visible task always provides
multiple aligned markers, so the implementation resolves that case as a
horizontal axis by row-first precedence.
