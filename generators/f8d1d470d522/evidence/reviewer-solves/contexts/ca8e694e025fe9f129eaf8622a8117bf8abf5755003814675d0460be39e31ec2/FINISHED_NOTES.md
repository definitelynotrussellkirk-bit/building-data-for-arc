# Solve work log

## Exposure declaration

This is the required post-repair solve, not a blind solve. I had earlier exposure
to the task rule while reviewing the generator. During this final-source episode I
used only the newly prepared visible examples and my own Python; I did not consult
the Racket rule, generator implementation, canonical/reference solutions, private
query labels, or the archived prior solve.

## Visible-pair hypothesis

Each input has exactly two color-9 markers embedded in a branching color-8 route
network and one or more color-7 obstacles. The output changes only route cells from
8 to 9. Comparing the visible pairs suggests:

1. A color-8 cell sharing an edge with a color-7 obstacle is unavailable.
2. Among remaining 8/9 cells, connect the two 9 markers by a shortest path.
3. If shortest paths tie in length, choose the one with the fewest direction
   changes (turns).
4. Leave the obstacle and all unselected route cells unchanged.

I implemented Dijkstra search over `(cell, incoming direction)` with a lexicographic
cost `(steps, turns)`. A coordinate-path key is used only to make any tie beyond the
visible rule deterministic. That final tie behavior is not established by the
visible examples, but it does not alter any example where shortest length and turn
count select a unique route.

## First revision

The first revision validates the rectangular grid, finds the two markers, disables
only color-8 cells cardinally adjacent to 7, searches the legal network, and paints
the selected route 9. I expect all five visible training examples to pass. If a
visible mismatch appears, I will inspect whether the discrepancy is obstacle
adjacency, turn counting, or a still-hidden final tie-break rather than changing
multiple assumptions together.
