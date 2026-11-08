# Solve work log

## Prior exposure

Before this blind episode I had not opened task `2e663d812b7a`'s generator,
Racket rule, notes, reference solutions, labels, or prior solve explanations.
I had only read the packet workflow and this episode's visible
`challenge.json`.

## Revision 1 — concentric square-ring interpretation

The first row is a compact key and the all-5 second row is a separator.  In all
three demonstrations, the first key color appears once below the separator and
acts as a center.  The later key entries are square rings at increasing
Chebyshev radius: `[8,1,2,6]` becomes center 8, then rings 1, 2, and 6; `[1,4]`
becomes a 4 ring around the 1.

The second demonstration also contains an interior zero in the key and repeated
2s.  Treating the key as extending through its last nonzero cell explains both:
the zero is a real blank ring, while only zeroes after the last nonzero are
padding.  Exact rings of radii 1 and 2 with the same color merge into the shown
thick 2 region.

That demonstration's center is close to the separator.  Rings that cannot fit
fully in the lower drawing field are clipped rather than overwriting the key or
separator.  Their nonzero key entries are replaced by separator color 5 in row
0; this exactly explains why key positions 2, 3, and 5 become 5 while the
interior zero at position 4 remains zero.  I generalized the same marker to any
edge of the lower field, although the visible examples only exercise the top
edge.

Implementation copies the grid, finds the key through its last nonzero entry,
finds the matching center color below row 1, and writes each exact square ring
only in rows 2 and below.  Remaining uncertainty: the examples contain one
center, so drawing around every matching center is a conservative extension not
explicitly demonstrated.
