# Solve notes — b8d6fabb411e post-repair episode

This is an exposed solve: I had already inspected the generator and rule during
repair work, but after `solve_episode.py prepare` I used only the printed visible
examples and did not reopen the generator, Racket source, labels, or references.

## Hypothesis

The solid block of color 3 is the anchor. For every other nonzero singleton:

- if its row lies anywhere within the anchor's row span, extend that marker's
  color horizontally through the black cells to the nearest vertical edge of
  the anchor;
- if its column lies anywhere within the anchor's column span, extend vertically
  to the nearest horizontal edge;
- leave diagonally offset markers unchanged.

The marker and the color-3 block remain unchanged. This explains all additions
in the four visible demonstrations, including interior-span rows/columns of the
3x3 anchor, so the rule is not restricted to boundary rows or columns.

## Implementation

Find the bounding box of all color-3 cells, copy the grid, then scan every
nonzero non-3 cell and fill the exclusive gap to the anchor only when the row or
column is in the anchor span. No revision was needed before the first check.
