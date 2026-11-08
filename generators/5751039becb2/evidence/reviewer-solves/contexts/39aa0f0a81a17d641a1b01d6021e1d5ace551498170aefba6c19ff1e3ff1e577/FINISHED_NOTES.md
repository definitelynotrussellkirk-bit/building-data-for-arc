# Post-repair blind solve notes

## Visible-example hypothesis

For every nonzero cell, inspect only its four diagonal neighbors (NW, NE, SW, SE).
Keep the cell when at least one diagonal neighbor has the same color; otherwise replace it with 0.
Zeros remain 0 and the grid shape is unchanged.

This explains the visible removals:
- isolated colors disappear;
- a same-colored orthogonal pair disappears because cardinal adjacency does not count;
- every member of a same-colored diagonal pair or three-cell diagonal chain remains.

## Intended check

Apply the rule independently to each input cell using the original input grid (not an incrementally modified grid).
