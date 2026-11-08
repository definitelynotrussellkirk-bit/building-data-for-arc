# Solve work log

Earlier exposure: no exposure to this task's Racket rule, generator, solutions, labels, or prior explanations. Before solving I read only the packet-wide instructions and `solve-blind/challenge.json`.

## Revision 1 — odd-by-odd rectangle center

Visible examples contain separated monochrome hollow rectangles. Every rectangle whose bounding-box height and width are both odd gains exactly its unique center pixel in the rectangle's color: 3x3, 3x5, and 3x7 examples change. Rectangles with an even dimension (4x5 or 3x4) remain unchanged because they have no single center cell.

Implementation hypothesis: find each 4-connected nonzero component, compute its bounding box, and color the unique bounding-box center only when both dimensions are odd. This also leaves all border pixels and all even-dimensional objects intact.

Probe: applied `solve()` to all three visible training inputs and compared exact grids to their visible outputs. All three matched. Remaining uncertainty: the visible objects are clean hollow rectangles; the implementation deliberately uses connected-component bounding boxes rather than requiring a perfect border, because the demonstrated semantic distinction is unique center existence.
