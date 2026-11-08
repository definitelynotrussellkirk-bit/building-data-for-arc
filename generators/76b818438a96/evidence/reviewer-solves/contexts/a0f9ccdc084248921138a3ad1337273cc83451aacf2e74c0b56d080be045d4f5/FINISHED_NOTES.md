# Post-repair visible-only solve notes

Earlier exposure: yes. I repaired this generator before this solve, so this is not blind. During the solve phase I used only the visible examples printed by `review.py solve prepare`; I did not reopen generator code, Racket, private labels, reference solutions, or earlier solution explanations.

## Hypothesis from visible pairs

Each input contains two one-cell-wide, nonbranching colored paths plus two singleton marker colors. For a path, exactly one endpoint has a singleton marker on the straight ray continuing outward from that endpoint.

Let `k` be the number of zero cells strictly between that endpoint and marker.

1. Fill those `k` cells with the original path color, joining the path up to the marker without overwriting the marker.
2. Starting at the path's *other* endpoint, follow the unique path inward and recolor its first `k` cells with the marker color.
3. Leave all remaining cells unchanged.

Visible checks:
- Example 0: the upper marker has a three-cell gap and recolors three cells at the opposite end; the lower-right marker has a two-cell gap and recolors two cells.
- Example 1: the two gaps are four and two cells, matching the recolored opposite-end prefixes.
- Example 2: the gaps are five and one cells, again matching the opposite-end recoloring lengths.

## Implementation

I find same-color 4-connected components, classify singleton components as markers and larger components as paths, detect degree-one endpoints, find a marker on an endpoint's outward ray, bridge the gap, and traverse the simple path from the opposite endpoint for the matching recolor count.
