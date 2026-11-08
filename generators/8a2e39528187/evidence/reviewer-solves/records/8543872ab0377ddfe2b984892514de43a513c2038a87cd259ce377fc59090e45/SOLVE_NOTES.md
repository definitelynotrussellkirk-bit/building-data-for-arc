# Solve work log

I had no earlier exposure to task `8a2e39528187`, its generator, rule, labels,
or prior solutions before this blind attempt.

## Revision 1 — area-coded recolouring

Across all four visible pairs, each nonzero monochromatic 4-connected object
keeps its exact shape and position.  Its output colour depends only on object
area: area 2 becomes colour 2, area 3 becomes 4, area 4 becomes 6, and area 5
becomes 8.  This is the formula `2 * (area - 1)`.  Input colour and scan order
are irrelevant; train example 3 is especially useful because the even input
colours are permuted rather than merely incremented/decremented.

I implemented a 4-neighbour flood fill for each nonzero monochromatic component,
then recoloured all cells in that component by the formula above.  Remaining
uncertainty: the visible domain contains only areas 2 through 5, so behavior for
other areas is extrapolated by the same formula.  The two query inputs also use
only those observed areas.
