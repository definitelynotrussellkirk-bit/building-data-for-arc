# Solve work log

Earlier exposure before this solve: none. I did not inspect any generator, Racket
rule, canonical source, prior solution, audit evidence, or private query label.

## Visible-example observations

All examples preserve the grid size and the counts of colors 0, 2, 5, and 7.
Each green `5` is an endpoint of a straight red `2` rod. A black `0` lies inside
the rod, with some red cells continuing beyond it. The output leaves the segment
from `5` through `0` fixed, removes the red tail beyond `0`, and redraws that tail
at 90 degrees around the `0`. The bend points toward the geometric center of the
grid: left-side vertical rods bend right, right-side rods bend left, and the
horizontal rod below center bends upward.

Concrete checks:

- Train 1, right rod: four cells below its pivot become four cells left of it.
- Train 1, left rod: one cell below its pivot becomes one cell right of it.
- Train 2, left vertical rod: four cells above the pivot become four cells right.
- Train 2, horizontal lower rod: its one-cell left tail becomes one cell upward.

I considered a fixed clockwise/counter-clockwise rotation, but the examples use
both senses. “Toward the center” explains every direction and avoids that rival.

## Implementation

For every `5`, search each cardinal direction for red cells followed by a `0` and
at least one red tail cell. Preserve the endpoint-to-pivot core, erase tail-only
cells, then choose the perpendicular direction whose rotated cells are closest
to the grid center (with bounds/collision tie-breaking). This also protects a
core cell if two rods cross.

The initial scaffold failed the visible harness with `NotImplementedError`, as
expected. The next revision implements the center-directed bend hypothesis.
Remaining uncertainty is limited to a pivot exactly on the center line; the code
uses total center distance and collision/bounds tie-breaking in that case.
