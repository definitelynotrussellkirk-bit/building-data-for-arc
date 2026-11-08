# Solve notes — ad9405621c3d

## Visible evidence

Each input uses black `0`, gray `5`, and exactly two cells of one other color.
Gray cells are unchanged in every output. The changed black cells form one
orthogonally connected corridor joining the matching colored cells, and every
new corridor cell uses that endpoint color.

The second training example rules out a straight-line or bounding-box fill: its
color-7 route must turn repeatedly around gray blockers. The third and fourth
examples show that only one connecting route is painted; unrelated reachable
black regions remain black.

## Hypothesis

Treat color 5 as impassable walls. Find a shortest orthogonal path from the
first row-major endpoint to the second through zero cells, then recolor every
cell on that path with the endpoint color. Use deterministic neighbor order
up, down, left, right when shortest paths tie; this is consistent with all four
visible outputs.

## Revision 1

Implemented row-major endpoint discovery and U/D/L/R breadth-first search.
The program copies the grid, preserves all walls and off-path zeros, and paints
only the recovered parent chain. No reference implementation or hidden label
was consulted during this solve phase. I had already seen the rule while doing
the assigned generator review, so this is an exposed post-repair solve, not a
blind solve.
