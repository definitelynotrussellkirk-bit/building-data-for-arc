# Solve work log

## Exposure declaration before solving

I had not opened task `48fee61713bb`'s generator, canonical rule, solutions,
private labels, prior solve explanations, or audit records. I had only read the
packet-level instructions and `solve-blind/challenge.json`.

## Hypothesis 1: decode, then gravity

Each input is a 30x30 rendering of a 7x7 colored grid. A logical nonzero cell is
shown as a hollow 3x3 square, with one-cell gaps between logical cells. The solid
line of color 1 marks one outer side. Removing that line leaves the logical cell
windows at offsets `1 + 4*k` on both axes.

Compressing the three training inputs this way produced 7x7 grids. Their outputs
were exactly obtained by stable gravity on each row or column, followed by
cropping empty outer rows/columns:

- marker on the right -> gravity down;
- marker on the bottom -> gravity left;
- marker on the left -> gravity up.

These are successive clockwise rotations, so the unshown fourth case should be
marker on top -> gravity right. Stable gravity preserves the order of colored
cells along the movement axis. I checked the claim manually on every column of
training example 1 and every row of training example 2; the observed sequences
and padding matched exactly.

## Implementation choice

The solver detects the marker side, removes only that border, reads each 3x3
logical-cell window, applies the corresponding stable gravity direction, and
crops the nonzero bounding box. It rejects mixed-color logical windows rather
than guessing. No reference material was consulted.
