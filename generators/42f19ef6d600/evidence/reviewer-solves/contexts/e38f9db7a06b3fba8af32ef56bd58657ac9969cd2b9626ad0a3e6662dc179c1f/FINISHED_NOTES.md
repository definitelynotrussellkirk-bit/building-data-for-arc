# Solve work log

I had not seen task `42f19ef6d600`, its generator, its Racket rule, any private
labels, or an earlier solution explanation before this blind episode. I used only
`solve-blind/challenge.json` and the public checker.

## Revision 1 — local right-angle emitters

### Observations

- The background is 7 and the added annotation color is 2.
- A filled 3x3 block gains a one-cell orthogonal fringe, excluding diagonal
  corner cells.
- A hollow rectangular frame gains marks only outside its four turning pixels,
  not beside straight edge-interior pixels.
- Isolated straight horizontal and vertical segments remain unchanged.
- A filled 2x2 block gains the same orthogonal fringe as the filled 3x3 block.

### Hypothesis

A non-background cell is active when it has at least one vertical and one
horizontal orthogonal neighbor of its own color. In other words, it participates
in a same-colored right-angle turn (including cells with three or four same-color
neighbors). For every active cell, replace each orthogonally adjacent background
cell with color 2. Detect activity from the original grid so newly written 2s do
not cascade.

This single local rule distinguishes frame corners from frame-edge interiors and
straight line segments without needing component-specific rectangle detection.

### Implementation and uncertainty

`solution.py` infers the background as the modal input color, preserves all input
cells, and applies the rule simultaneously. The examples fix the emitted color as
2. Remaining uncertainty is limited to unseen inputs in which color 2 is already
part of an object or the background is not the modal color; neither case is
suggested by the visible examples.
