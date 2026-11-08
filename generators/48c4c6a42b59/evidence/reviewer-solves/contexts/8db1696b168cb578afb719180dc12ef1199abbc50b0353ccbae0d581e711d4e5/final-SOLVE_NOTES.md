# Solve notes — 48c4c6a42b59

## Visible-example observations

- Grid size and background remain unchanged.
- Every nonzero color forms its own connected object.
- Output never deletes an input cell; it only adds cells of the same color.
- Additions make each object left-right symmetric inside that object's tight column span, not around the full canvas.
- Example 1 is decisive: the purple object at the left and the yellow object at the right use different local reflection axes in the same grid.
- Example 2 rules out “transform one selected color/object”: all three objects are completed.
- Example 3 rules out vertical reflection and bounding-box fill: the additions are row-preserving horizontal reflections, while holes not implied by reflection remain holes.

## Hypothesis

For each 4-connected same-color nonzero object independently:

1. Find its minimum and maximum occupied columns.
2. Keep every original cell.
3. For every object cell `(r, c)`, add the same color at `(r, min_col + max_col - c)`.

## Implementation choice

I used same-color 4-connectivity so separate objects are not accidentally joined by diagonal contact or by sharing a color elsewhere. The transformation is computed from the original object cells, and the output starts as a deep copy, which preserves originals exactly.

## Competing ideas rejected from visible data

- Global horizontal reflection: different objects in one grid have different local axes.
- Replace by the mirror: original asymmetric cells remain.
- Vertical reflection: added cells remain on the same rows.
- Fill each bbox: several output holes remain.
- Transform only the first/largest/a special color: every object changes in the demonstrations.
