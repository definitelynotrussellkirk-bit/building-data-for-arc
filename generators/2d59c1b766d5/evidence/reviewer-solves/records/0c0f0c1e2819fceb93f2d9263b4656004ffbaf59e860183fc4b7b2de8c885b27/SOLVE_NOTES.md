# Post-repair visible solve notes

## Hypothesis

Each 8-colored rectangular border is an independent chamber. Inside each
chamber, the single nonzero/non-gray cell is a gate and color source. Replace
only zero cells connected to that gate by four-neighbor paths that remain
strictly inside the frame and do not cross gray 5 walls. Preserve unreachable
zeros, walls, borders, and the exterior.

## Evidence from visible examples

- Example 1 has full gray barriers. Zeros on the gate side are colored while
  the opposite side remains zero, so filling all non-wall cells is wrong.
- Examples 2 and 4 contain bent/stepped walls. The output respects orthogonal
  reachability rather than diagonal corner crossing.
- Every frame uses its own gate color, and frames do not interact.

## Implementation

Find 4-connected color-8 frame components, use each component's bounding box,
find the interior gate, and BFS through cells whose original value is either
zero or the gate color. Paint the visited set only.
