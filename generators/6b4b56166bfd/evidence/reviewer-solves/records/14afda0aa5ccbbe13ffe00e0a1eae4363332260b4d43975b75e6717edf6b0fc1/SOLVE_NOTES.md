# Solve notes

The visible examples all contain one color-5 pivot and one or more isolated
colored cells.  Relative to the pivot, every colored cell is reproduced at the
other three quarter-turn positions: `(dr, dc)`, `(dc, -dr)`, `(-dr, -dc)`, and
`(-dc, dr)`.  Color 5 stays fixed, zeros stay zero, and rectangular examples
show that the rotation is around the pivot rather than around the grid's
bounding box.  I therefore copy the input and stamp each nonzero, non-5 seed at
all in-bounds members of its four-position orbit.

No alternate visible-example hypothesis was needed for this revision.  The
solve is not blind with respect to the broader review: I had earlier rule
exposure while repairing this generator, which will be declared at finish.
