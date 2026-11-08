# Solve notes

## Visible-example hypothesis

Each nonzero color is one object. Ignore its absolute input position and
translate its occupied cells so the object's own bounding-box top-left is
coordinate `(0, 0)`. Overlay the two normalized cell sets in the smallest box
covering their union:

- a cell occupied by both normalized objects becomes `9`;
- a cell occupied by exactly one object keeps that object's color;
- an unused cell inside the union bounding box is `0`.

The three demonstrations match this exactly. Their outputs are compact despite
large physical separation, which rules out preserving input offsets. The
asymmetric 2×4 versus 4×2 operands also show top-left rather than bottom-right
alignment.

## Implementation

`solution.py` extracts the two colors, normalizes each cell set independently,
and renders the union. It does not assume which object is physically left,
right, above, or below. Color sorting is only used to name the operands; the
operation is symmetric except for retaining each object's own color.

## Exposure record

This is the required post-repair solve. I had already seen the generator and
canonical rule while repairing the assigned task, so this attempt is not blind.
I did not reopen or consult a reference while writing this solver after
`solve prepare`; the implementation follows the displayed examples.
