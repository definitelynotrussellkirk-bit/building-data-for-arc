# Solve work log

Earlier exposure: none. I did not open any generator, canonical rule, reference
solution, private query label, or prior solve explanation before this attempt.

## Revision 1 — containment-depth recoloring

The visible examples preserve all occupied cells and only change their colors.
Large outer shapes become color 2; a separate component whose bounding box lies
inside an outer component becomes color 3; an object inside two nested components
becomes color 4, and the four-level example continues to color 5. Side-by-side
frames both start at depth zero. The open L-shaped example suggests that the
relation is rectangular/bounding-box containment rather than flood-fill enclosure.
The differently colored cell replacing the outer frame's corner in train example
2 is still inside the larger component's bounding rectangle and therefore has
one containing object.

Implementation: split nonzero cells into monochromatic 4-connected components,
compute each component's bounding box, count strictly larger component boxes that
contain it (allowing contact with the containing box boundary), and recolor the
component as `2 + count`. Background remains zero.

Main uncertainty: a component could theoretically have the same bounding box as
another disconnected component, or overlapping non-nested boxes. Neither occurs
in the visible examples or queries; requiring a strictly larger box prevents a
mutual-containment cycle.
