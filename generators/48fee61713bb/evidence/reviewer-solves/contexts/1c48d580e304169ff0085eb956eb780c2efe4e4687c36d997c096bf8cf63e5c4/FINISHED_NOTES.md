# Solve work log

## Exposure declaration before solving

I had not opened task `48fee61713bb`'s generator, canonical rule, notes, prior
solutions, audit records, or private labels. I had only read the packet-level
instructions and the visible `solve-blind/challenge.json`.

## Revision 1 — decode, rotate the wall direction, and compact

The 30x30 grids are a magnified 7x7 logical board. Every occupied logical cell
is drawn as a hollow 3x3 square; neighboring logical cells are four pixels apart.
The solid line of color 1 lies on exactly one outer edge and shifts the lattice
one cell farther inward when it is on the top or left.

I reduced each training input to a 7x7 color matrix by sampling the upper-left
corner of each possible 3x3 square. I then tested independent stable compaction
of each row or column in all four directions. The exact matches were:

- right-edge line -> compact every column downward;
- bottom-edge line -> compact every row leftward;
- left-edge line -> compact every column upward.

Thus the line indicates a direction that is rotated 90 degrees clockwise to get
the packing/gravity direction; the unseen top-edge case should pack rightward.
After packing, removing wholly empty outer rows and columns reproduces all three
visible outputs exactly. The program implements all four orientations, preserves
the order of colored cells within each row/column, and does not special-case the
training colors.

A plausible alternative was packing toward the color-1 edge itself, but it fails
all visible examples. Another was rotating the board before packing, but direct
stable compaction already explains output orientation and dimensions.

Remaining uncertainty: the top-edge orientation is extrapolated from the clean
four-way rotational pattern rather than shown in the three training pairs.
