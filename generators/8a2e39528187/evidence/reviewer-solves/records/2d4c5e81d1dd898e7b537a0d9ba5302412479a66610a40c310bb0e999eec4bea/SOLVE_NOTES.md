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

## Revision 2 — rank objects, not absolute area

The first check passed 3/4 visible examples.  The mismatch was train example 1,
which contains two area-2 objects.  The left area-2 object becomes colour 2 and
the right area-2 object becomes colour 4, while the area-4 and area-5 objects
become 6 and 8.  Thus the colors encode the objects' ascending area rank rather
than the formula applied independently to each area.  For equal areas, the
visible evidence orders the objects by top-left scan position.  I changed the
solver to collect all components, sort by `(area, top-left cell)`, and assign
2, 4, 6, ... by rank.  This preserves the successful behavior on examples with
distinct areas and resolves the observed tie.
