# Solve work log

## Isolation / prior exposure

I had not opened task `249b59452da6`'s generator, Racket rule, reference
solutions, private query labels, prior solution notes, or audit records. I used
only `solve-blind/README.md`, `solve-blind/challenge.json`, and local Python
probes over the visible examples.

## Revision 1 — concave-corner fill outside the marked component

Initial visual hypothesis: green `3` cells complete concave corners in red `2`
arrangements. I enumerated every zero cell with at least two orthogonal red
neighbors. This produced every green output cell, plus exactly two unchanged
candidates in train 0, two in train 1, and two in train 2.

The unchanged candidates were not selected by corner orientation: the added set
contains all observed NW/NE/SW/SE orientations and three-neighbor cases. Instead,
every unchanged candidate touched the red object containing the duplicated
non-red diagonal marker pair (`9`, `7`, or `6`). The singleton `8` in train 2 is
a distractor. A 4-connected component split the diagonal marker cells; an
8-connected component over red plus the duplicated marker color grouped the
intended exemplar object and excluded exactly the six unchanged candidates.

Implemented rule:

1. Find the non-red color occurring exactly twice as a diagonally adjacent pair.
2. Find its 8-connected component through cells colored red `2` or that marker.
3. Copy the grid. For every zero with at least two orthogonal red neighbors,
   paint it green `3` unless those red neighbors belong to the marked component.
4. Preserve the marker pair and any unrelated distractor colors.

Pre-implementation test: a visible-example harness importing the supplied stub
failed with `NotImplementedError`, as expected. Remaining uncertainty is limited
to unseen inputs containing multiple duplicated non-red colors; the visible
contract uniquely identifies the diagonal duplicated pair and all demonstrations
are explained without exceptions.
