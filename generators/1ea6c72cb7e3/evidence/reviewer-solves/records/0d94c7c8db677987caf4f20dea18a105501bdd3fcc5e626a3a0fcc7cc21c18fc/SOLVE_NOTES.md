# Blind solve notes — task 1ea6c72cb7e3

## Visible evidence and hypothesis

The gray (`5`) cells act as opaque walls.  Every other nonzero input cell is a
colored point marker.  Each marker projects its color horizontally and
vertically through the maximal open row/column segment containing it; projection
stops immediately before a gray wall or at the grid edge.  Original gray cells
and marker cells are preserved.  An empty cell reached by exactly one marker
gets that marker's color; an empty cell reached by two or more markers becomes
`8`.

Evidence:

- In training example 1, markers `9` and `1` share a row.  Their overlapping
  horizontal projections turn the rest of that row into `8`, while their source
  cells remain `9` and `1`.
- In training example 2, the `4` and `3` projections stop at the gray vertical
  wall and gray horizontal wall.  Their crossings with each other and with the
  `2` projection are `8`.
- In training example 3, the three markers project to grid edges unless the gray
  H-shaped structure blocks them; the three pairwise crossings are `8`.

## Implementation choice

Track the set of marker identities reaching every cell, rather than only colors.
This handles overlapping collinear projections as well as perpendicular
crossings.  Source markers have priority over projected intersections, matching
training example 1.  Only input gray cells block a ray; other markers do not.

## Test-instance expectations

The first query has two same-column marker pairs (`9`/`2` and `1`/`6`), so the
shared portions of those columns should become `8`, except at source markers.
The second query is split by the gray cross: left-side markers cannot project
through column 4 or row 5, while the far-right `1` projects within the right
region and vertically to both edges.
