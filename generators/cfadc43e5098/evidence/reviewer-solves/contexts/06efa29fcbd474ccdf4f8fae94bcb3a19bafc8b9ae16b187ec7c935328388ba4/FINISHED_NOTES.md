# Solve work log

## Exposure statement

Before this blind solve I had not opened task `cfadc43e5098`'s generator, Racket rule,
private labels, reference solution, audit evidence, or prior solution notes.  I used
only `solve-blind/challenge.json`, the public preparation output, and my own Python
summaries of those visible grids.

## Revision 1

### Initial observations

The inputs contain separated solid rectangular objects on a zero background.  The
outputs preserve every original cell and add only colour 8.  In each example the new
8s form rectangular bridges between same-colour objects that overlap in rows or
columns.  The bridge is inset by one cell from each end of the shared perpendicular
span.  For example, two rectangles sharing rows 4--9 receive a horizontal bridge on
rows 5--8; a four-row overlap receives a two-row bridge.

### First hypothesis and probe

I first tested the rule "join every same-colour pair whose row or column projections
overlap by at least three cells."  A local comparison reproduced training examples 0
and 1 exactly but overfilled 12 cells in training example 2.  The extra cells came
from directly joining a top rectangle to a farther lower rectangle even though a
closer same-colour rectangle lay between them.

### Revised hypothesis

For each object and each cardinal direction, select the nearest same-colour rectangle
whose perpendicular projection overlaps by at least three cells.  Join each selected
pair through the blank gap with colour 8, using the overlap interval with its two
outermost rows or columns removed.  Preserve all original nonzero cells.  Tied nearest
objects are all retained, although no visible example requires the tie case.

### Local visible-example check

I parsed 4-connected nonzero components, compared their bounding boxes, generated the
nearest-neighbour bridges, and compared every output cell against all three visible
training outputs.  The revised hypothesis matched all three exactly with zero cell
differences.  Remaining uncertainty is limited to unseen tie-breaking or malformed
non-rectangular objects; the visible examples consistently use solid rectangles.
