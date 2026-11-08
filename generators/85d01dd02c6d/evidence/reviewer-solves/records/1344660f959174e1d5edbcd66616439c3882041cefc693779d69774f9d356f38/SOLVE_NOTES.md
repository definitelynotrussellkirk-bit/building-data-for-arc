# Post-repair solve notes

This is a human work log based on the visible examples in `challenge.json`. I had earlier exposure to the intended rule while repairing the generator; I did not consult the Racket rule, generator source, reference solutions, or private query labels during this solve episode.

## Hypothesis

- Cells colored 9 are opaque walls and remain 9.
- Every other nonzero cell is a seed; the seed's original color does not otherwise matter.
- A seed casts a ray through its own cell and in all four cardinal directions, stopping before a 9 wall or the grid boundary.
- Count visibility by *distinct seeds*. A non-wall cell becomes 8 when at least two seed rays include it; every other non-wall cell becomes 0.
- Colored seeds do not block rays. This explains the full column of 8s through both aligned seeds in train example 1.

## Checks against visible examples

- Train 0: the two marked cells are the two perpendicular ray intersections in the upper chamber; the full horizontal wall prevents any upper/lower interaction.
- Train 1: the two seeds in column 4 illuminate the whole column twice, including both seed cells. The right seed's vertical ray intersects the lower seed's horizontal ray at `(7, 6)`. The short wall blocks the left/right same-row seeds.
- Train 2: the upper-left and upper-right seed rays intersect twice; the lower seed is isolated by the full horizontal wall.

The implementation counts each seed at most once per cell, preserves every wall cell, and validates rectangular input.
