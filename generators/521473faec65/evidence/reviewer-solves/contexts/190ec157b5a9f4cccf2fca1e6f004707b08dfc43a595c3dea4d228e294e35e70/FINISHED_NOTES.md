# Solve notes

## Hypothesis

Each nonzero connected object is a solid monochrome rectangle. Replace each
rectangle independently by a checkerboard over its bounding box. The object's
top-left cell is retained, then cells alternate by local row-plus-column parity;
all removed cells and the original background are 0.

## Visible-example checks

- Example 0 has three objects. All three are transformed, so the rule is not
  limited to two objects. The color-5 rectangle starts at `(0,7)` and keeps that
  cell even though its global coordinate sum is odd, so phase is local to each
  rectangle rather than fixed at the grid origin.
- Examples 1 and 2 preserve each object's color and shape bounds while removing
  alternating cells.
- The implementation finds same-color 4-connected components, obtains each
  component bounding box, and paints cells with even local offset parity.

No reference implementation or private output was consulted during this solve.
Earlier rule exposure is necessarily yes because this is the required
post-repair solve.
