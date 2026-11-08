# Solve work log

## Prior exposure

I had not opened this task's generator, Racket rule, reference solution, private labels,
audit records, or earlier solution explanation. Before solving I only read the packet's
general review instructions and the visible examples printed by `blind prepare`.

## Revision 1 — rectangle-perimeter completion

**Observation.** Every nonzero color occurs exactly four times. For each color, the
four cells occupy the Cartesian product of two row coordinates and two column
coordinates: the corners of an axis-aligned rectangle. The output retains the
corners and fills all cells on that rectangle's top, bottom, left, and right edges.
Interior cells remain zero. Degenerate thickness-two rectangles consequently become
fully filled, matching color 2 in train 0 and color 9 in train 1.

**Probe.** I checked the bounding boxes and output color counts mentally across all
three visible examples. I then ran a visible-training harness against the untouched
starter; it failed with `NotImplementedError`, establishing the test before the
implementation.

**Program.** Scan nonzero cells by color, compute each color's minimum/maximum row
and column, copy the input, and paint the four bounding-box edges.

**Alternatives considered.** Filling each bounding box solid is contradicted by all
rectangles wider and taller than two cells. Extending line segments only in one
orientation is contradicted by the completed four-sided borders.

**Remaining uncertainty.** The visible examples contain no intersecting rectangle
perimeters. The implementation uses first-seen color insertion order if two generated
perimeters claim the same previously blank cell; the intended data appears to avoid
that undefined case.
