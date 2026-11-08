# Solve notes — 531e65dffc0a

This is a human work log for the exposed post-repair episode. I had already read the task's generator and selected rule while repairing it, so this is **not blind**; I did not reopen those sources during this solve.

## Visible-example inference

- Each input has one connected monochrome object whose color is not 2, 3, 4, or 5. I treat its bounding-box-normalized cells as a prototype.
- The remaining nonzero singleton cells are anchors. Their colors encode rotations of the prototype:
  - 2: identity.
  - 3: 90° clockwise.
  - 4: 180°.
  - 5: 90° counter-clockwise.
- Each transformed shape is normalized back to its own top-left bounding-box corner, then that corner is placed at the anchor coordinate.
- The output begins as an all-zero grid of the same size. Stamps use the prototype color; the source prototype and anchor colors are not copied. Any transformed cell outside the grid would be clipped.

## Checks against the visible training pairs

1. In training pair 1, code 2 reproduces the lower-left-oriented three-cell prototype, while code 3 produces its clockwise orientation. Both are painted in color 8 on a blank canvas.
2. Training pair 2 exposes code 5 as the opposite quarter-turn and confirms that the anchor is the transformed bounding-box origin rather than necessarily an occupied prototype cell.
3. Training pair 3 includes code 4 and distinguishes the half-turn from identity on an asymmetric five-cell prototype.

## Implementation choice

The solver extracts same-color four-connected non-anchor components and chooses the largest, matching the visible notion of the exemplar. It then applies the four transforms geometrically and stamps all anchors into a fresh grid. One substantive revision was sufficient.
