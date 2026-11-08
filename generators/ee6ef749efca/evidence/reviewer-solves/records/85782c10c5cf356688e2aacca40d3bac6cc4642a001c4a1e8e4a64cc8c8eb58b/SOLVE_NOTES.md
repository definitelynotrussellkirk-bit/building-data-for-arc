# Solve work log

## Exposure declaration

Before this blind episode I had not opened task `ee6ef749efca`'s generator,
reference rule, notes, prior solves, or private labels. I used only
`solve-blind/challenge.json` and the visible checker.

## Revision 1 — largest-object stamping

Observation: every training output is blank except for copies of one magenta
(color 6) object placed at red (color 2) cells. The red cell is the top-left
occupied cell of the copied object's normalized bounding box. Original magenta
objects and red anchors disappear.

The first and third examples have one magenta component. The second has a
five-cell component and a three-cell vertical distractor; only the five-cell
component is copied. This supports selecting the largest 4-connected magenta
component, preserving its orientation, normalizing by its minimum row/column,
and stamping it at every red anchor. Overlapping copies are unioned.

Implemented that rule with deterministic component extraction. The generated
examples place copies in bounds; the implementation clips defensively at grid
edges rather than changing shape orientation.

Remaining uncertainty: demonstrations do not distinguish 4-connectivity from
8-connectivity for diagonal-only contacts, nor specify tie-breaking between
equal-sized magenta components. The implementation uses 4-connectivity and
row-major deterministic selection for a tie.
