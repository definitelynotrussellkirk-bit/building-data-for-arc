# Solve work log

## Exposure declaration

Before this blind solve I read only the packet-level directions and the visible
challenge prepared in `solve-blind/`. I did not open this task's generator,
Racket rule, private labels, prior solutions, notes, or audit records.

## Observations and hypothesis

The cell at `(0, 0)` is isolated from a second nonzero component. Removing that
cell and tightly cropping the second component accounts for every output color
and output dimension. I compared all eight rectangular dihedral transforms of
the cropped component against the three demonstrations:

- instruction color `1`: 90-degree clockwise rotation;
- instruction color `2`: 180-degree rotation;
- instruction color `3`: main-diagonal transpose.

A small local Python comparison confirmed exact equality for all three visible
outputs. The payload may contain internal zeroes, so the crop uses the bounding
box of nonzero payload cells and preserves every zero inside it.

## Underdetermination and decision for color 4

The second query uses instruction color `4`, but no demonstration defines that
symbol. Its transform is therefore not identifiable from the visible examples
alone. Several programs agree on every demonstration and disagree on that query.
I chose anti-diagonal reflection as the minimal symmetric completion: the seen
set has two rotations and one diagonal reflection, and this adds the paired
diagonal reflection. Identity, counter-clockwise rotation, or an axis reflection
would fit the visible data equally well. This is a recorded uncertainty rather
than a claim that the private query is determined.

## Implementation

`solution.py` removes only the instruction pixel, crops the payload, and applies
a pure list-based transform. It has no dependency on NumPy or hidden task data.
