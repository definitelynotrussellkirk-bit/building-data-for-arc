# Visible-example solve log

## Hypothesis

Color `5` is an inert obstacle. Every other nonzero color occurs as two endpoint cells. For each pair, there are two orthogonal L-shaped Manhattan routes, one through `(row_a, col_b)` and one through `(row_b, col_a)`. Paint the route whose every cell is either background `0` or that pair's own color; leave all obstacles and unrelated endpoints unchanged.

## Evidence from the three demonstrations

- In demonstration 1, the `8` pair uses the upper-left elbow because the opposite route meets a gray obstacle, while the `3` pair uses the upper-right/lower-right elbow. The gray `5` cells are never extended.
- Demonstration 2 uses opposite route choices for `6` and `4`, showing that orientation is decided pair by pair rather than globally.
- Demonstration 3 has three pairs and blockers away from some candidate elbows. The output follows the complete clear route, so checking only the elbow is insufficient.

## Implementation choice

The solver groups all colors except `0` and `5`, constructs both candidate paths from the original input, selects the first fully clear path, and paints it into a copy. Clearance is tested against the original grid so one newly painted path cannot spuriously block another.
