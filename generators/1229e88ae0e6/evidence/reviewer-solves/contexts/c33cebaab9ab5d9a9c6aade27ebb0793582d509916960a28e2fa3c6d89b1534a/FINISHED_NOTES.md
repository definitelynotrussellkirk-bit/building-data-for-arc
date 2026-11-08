# Solve work log

I had not opened this task's generator, rule, notes, solutions, audit records, or
private labels before solving. I had only read the packet-level instructions and
`solve-blind/challenge.json`.

## Revision 1 — center the colored bounding box

Hypothesis: every example translates the complete nonzero pattern without rotation,
reflection, recoloring, or resizing so that its tight bounding box is centered in
the canvas. For an even leftover margin, both sides are equal; for an odd leftover
margin, integer floor places the extra blank row/column on the bottom or right.

Probe: I computed each visible bounding box and target origin as
`((grid_height - box_height) // 2, (grid_width - box_width) // 2)`:

- Train 1 shifts from `(3, 2)` to `(1, 2)`, matching `(-2, 0)`.
- Train 2 shifts from `(0, 1)` to `(1, 2)`, matching `(+1, +1)`.
- Train 3 shifts from `(1, 2)` to `(1, 1)`, matching `(0, -1)`.
- Train 4 shifts from `(3, 3)` to `(2, 1)`, matching `(-1, -2)`.

Rejected alternatives: moving objects away from the nearest edge and moving toward
a fixed anchor both fit subsets but not all four examples. The consistent invariant
is the centered tight bounding box while preserving every colored cell.

Predicted queries:

1. The 2x2 pattern shifts down two rows, from origin `(0, 2)` to `(2, 2)`.
2. The 2x3 pattern shifts down one and left two, from `(1, 4)` to `(2, 2)`.

Remaining uncertainty: all examples use background color 0 and one connected
nonzero pattern. The implementation treats all nonzero cells as one pattern, which
is the narrowest behavior supported by the visible examples.
