# Solve work log

## Boundary and prior exposure

This is the required blind-before-repair solve. Before writing the solution I had
not opened the generator, canonical rule, task notes, prior solutions, private
labels, or audit records for either the blind task or the assigned repair task.
I used only `solve-blind/challenge.json`.

## Attempt 1 — hollow rectangular frame

**Observation.** In every training pair exactly one green connected component is
recolored orange. The selected component is a complete one-cell-thick rectangular
outline with a nonempty interior: 3x3, 4x3, and 3x5 respectively. Other green
components are lines, irregular/partially closed outlines, or a 2x2 block with no
interior.

**Hypothesis.** Find each 4-connected green component. If its cells equal exactly
the border of its bounding rectangle and both bounding dimensions are at least
3, recolor that whole component from 3 to 7; preserve everything else.

**Probe/design.** The implementation explicitly compares each component with the
mathematical border set of its bounding box. This rejects the near-rectangle in
the second test input because its top edge has a gap, and rejects 2x2 blocks via
the nonempty-interior size requirement.

**Remaining uncertainty.** The visible examples do not distinguish “hollow
rectangle” from some more semantic description such as “the only regular closed
loop,” but exact rectangular-border matching is the simplest rule consistent
with all examples.
