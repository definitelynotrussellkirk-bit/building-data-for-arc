# Solve work log

I had not opened this task's generator, canonical rule, reference solution,
private labels, prior solve notes, or any assigned-generator source. Before this
step I had only read the packet-level instructions and the generated visible
`challenge.json`.

## Observation and hypothesis

Each input has a separated row of color-9 marker cells at the top and several
single-color connected objects below it. The output is an exact tight crop of
one lower object, with its color and internal background preserved.

I compared every lower component's occupied columns and vertical extent against
the marker columns. In training examples 1 and 2, only the returned object
intersects a marker column. In training example 3, four objects intersect marker
columns; their bottom rows are 13, 16, 13, and 18, and the returned color-7
object is the unique lowest one. This suggests:

1. retain lower connected components whose occupied columns intersect at least
   one top-row marker column;
2. choose the component with the greatest bottom row;
3. return its tight crop.

The first test has only the color-3 object aligned with a marker. The second test
has an upper color-6 object and a lower color-1 object aligned with markers, so
this rule predicts color 1. That second query is the strongest visible probe of
whether "lowest aligned object" rather than "most marker overlap" is intended.

## Implementation

`solution.py` finds 4-connected same-color components below the marker row,
filters by occupied-column intersection, selects the greatest bottom coordinate,
and renders only that component in its bounding box. Tie keys are deterministic
but are not supported as semantic claims; no training example needs them.

## Alternatives and uncertainty

I considered selection by maximum number of intersecting marker columns. It also
fits the demonstrations but would choose the upper color-6 object in test 2,
whereas the demonstrated multi-candidate case is resolved by vertical depth.
I therefore kept bottom position as the primary and explicit discriminator.
Another possible refinement is to use horizontal bounding-box overlap instead
of occupied-cell overlap; the demonstrations do not distinguish these, but the
visible objects make occupied-column alignment the more literal relation.
