# e8b6ff767c21 native parametric family

`route_overlay` controls a second stage after constructing the canonical green
spiral.

- `none` is the accepted canonical program byte-for-byte.
- `terminal_path` first constructs the same spiral walls, identifies the final
  green cell, then paints in blue the shortest open-corridor route from the
  outer entrance `(1, 0)` to an open neighbor of that terminal. The fixed
  neighbor order is right, down, left, up.

The two stages are causally linked: changing or omitting the spiral changes the
walkable cells and therefore the route. Inputs are blank rectangles and are
identical across settings. Episodes support 2--6 demonstrations and 1--4
queries; the fourth query is a 30x30 stress scene.
