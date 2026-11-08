# Solve work log

I had not opened the assigned generator, this task's generator, any Racket rule,
reference solution, private query label, prior solve explanation, or task-specific
notes before this blind solve. I used only the public grids printed by `blind prepare`
and the visible training pairs in `solve-blind/challenge.json`.

## Revision 1 — bounding-box center of each object

**Observation.** Every nonzero connected object disappears except for one pixel of
the same color. The retained pixel is not always the rounded centroid. In training
example 2, the color-3 object has arithmetic centroid column 5.8 but retains column
6; in training example 0, the top-right triomino has centroid column 5.67 but retains
column 5. Those two cases reject a single conventional centroid-rounding rule.

**Hypothesis.** For each same-color 4-connected object, compute its axis-aligned
bounding box and retain the top/left-biased center:
`((min_row + max_row) // 2, (min_col + max_col) // 2)`.

**Probe.** I checked this coordinate against all seven visible objects. It gives
(0,0), (2,5), and (6,1) in training example 0; (3,2) and (8,2) in example 1; and
(2,1) and (3,6) in example 2, exactly matching every visible output pixel. A local
visible-example regression first failed on the provided `NotImplementedError`, then
passed after implementing the rule.

**Alternatives considered.** Arithmetic centroid with floor fails the color-3 object
in example 2. Arithmetic centroid with nearest rounding fails the top-right triomino
in example 0. Choosing a geometric median or a pixel already present in the input is
also inconsistent because the retained bounding-box center need not be occupied.

**Remaining uncertainty.** The visible data supports 4-connected, same-color
components and background color 0. It does not distinguish 4- from 8-connectivity for
diagonally touching cells, but all demonstrated objects are ordinary 4-connected
shapes, so I used the standard 4-connected interpretation.
