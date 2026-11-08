# Solve notes — 5f5b990b28ab

This is a human work log for the required post-repair, exposed solve.  I had
already inspected the task while repairing its generator, so this is **not** a
blind solve.  During this solve phase I used only the visible examples printed
by `solve_episode.py prepare`; I did not reopen the generator, Racket rule,
reference helper, private labels, or earlier solution explanations.

## Visible-example observations

1. Grid shape and zero background are preserved.
2. Each 4-connected cyan/nonzero object is recolored uniformly; object cells do
   not move.
3. Nested example 0 gives colors 2, 4, 6 from largest enclosing box to smallest.
4. The disconnected examples distinguish the ranking feature:
   * train 1 has bbox areas 35, 32, and 21, receiving 2, 4, and 6;
   * train 3 has bbox areas 30, 28, 24, and 12, receiving 2, 4, 6, and 7.
   This rejects scan order, width, and cell-count/perimeter ranking.
5. Hypothesis: extract 4-neighbor nonzero components, rank by descending
   bounding-box area, then assign the fixed palette `[2,4,6,7,3,5,9]`.

## Implementation

`solution.py` performs an independent 4-neighbor flood fill, computes each
component's bounding box, sorts by descending area (bbox as deterministic tie
break), and paints the ranked objects into an otherwise-zero output grid.
