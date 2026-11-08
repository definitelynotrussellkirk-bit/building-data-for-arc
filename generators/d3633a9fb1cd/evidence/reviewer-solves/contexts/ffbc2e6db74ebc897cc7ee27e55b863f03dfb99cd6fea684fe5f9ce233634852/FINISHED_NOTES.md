# Solve notes

Earlier exposure: yes. I reviewed this task's generator and semantic contract before this required post-repair episode, but I did not reopen the generator, Racket rule, reference outputs, or private labels while solving this challenge.

## Visible-example hypothesis

Color 5 is an impassable wall. Every other nonzero cell is a colored seed. For each zero cell, compute four-neighbor shortest-path distance through cells that are not color 5. If exactly one seed is nearest, paint the zero with that seed's color. If the closest distance is tied, leave the cell 0. Components with no seed also stay 0. Walls and seeds are unchanged.

The first training example is the key discriminator: the interior color-5 finger changes shortest paths, and some equal-distance cells remain 0. The other two examples confirm that separately framed rooms do not exchange colors and a single seed fills its entire reachable room.

## Implementation

Run one BFS distance map per seed, then assign each original zero cell only when the minimum distance has one winning seed color. The solver copies the input and never mutates it.
