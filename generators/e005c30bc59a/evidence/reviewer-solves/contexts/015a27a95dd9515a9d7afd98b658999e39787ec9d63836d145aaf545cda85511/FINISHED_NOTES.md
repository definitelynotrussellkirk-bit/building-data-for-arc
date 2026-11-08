# Solve notes — e005c30bc59a

This is the required **exposed post-repair solve**. I had already inspected this task's rule and generator during repair, so earlier rule exposure is `yes`; I did not consult the Racket source, reference solution, private labels, generator code, or earlier solution explanations during this solve episode.

## Visible-example hypothesis

Across the four visible demonstrations:

- There is one non-corner border cell whose color is not 0, 1, 2, or 5. It is both the source and the paint color.
- The beam starts one cell inward from that border source.
- Black cells on the beam path are recolored to the source color.
- Color 1 behaves as `/`: `(dr, dc) -> (-dc, -dr)`.
- Color 2 behaves as `\\`: `(dr, dc) -> (dc, dr)`.
- Color 5 blocks the beam and is not recolored.
- Unreached mirrors and walls are distractors.

The fourth demonstration is the key ambiguity breaker: the route crosses a coordinate painted earlier, but approaches it from a different direction and continues to a new cell afterward. Therefore loop detection must use `(row, column, direction)`, not merely `(row, column)`, and tracing must inspect the original input rather than treating newly painted cells as obstacles.

## Implementation

`solution.py` locates the unique source, derives the inward direction, traces the original grid, paints only original zeros, reflects at 1/2, and stops at a wall, boundary, unexpected occupied cell, or repeated directional state.

No speculative special cases were added for grid size, source color, number of mirrors, or path shape.
