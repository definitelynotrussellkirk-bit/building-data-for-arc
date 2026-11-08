# Native parametric corner-composition family

`finish=corners_only` is byte-for-byte the selected canonical Racket rule.
For every same-color 4-connected component it erases the source cells and paints
only the four bounding-box corners in the component color.

`finish=nearest_corner_bridge` adds a genuine second step:

1. **A — corner extraction:** compute the canonical four-corner group for every
   input component and materialize the corner-only grid.
2. **Intermediate:** find the unique minimum-Manhattan pair of corners belonging
   to two different original components.
3. **B — bridge:** paint zero cells on the row-then-column Manhattan route between
   those two derived corners with color 4, preserving all corner markers.

The admitted grammar guarantees a unique closest pair. Inputs are identical
across settings for a matching seed/count request. Six deterministic demo
profiles and four query profiles support independent 2–6 demo and 1–4 query
counts; the last query is a substantive 30×30 case. The first two demos jointly
refute the retained finite rivals, including selecting original object cells
instead of A's corners, taking the other L bend, restricting to the first two
components, merging disconnected same-color components, and choosing the
farthest corner pair.

The protected-Racket causal witness uses `rules/nearest_original_cells.rkt` as a
`wrong_intermediate` ablation: it computes the canonical corner grid but chooses
bridge endpoints from the original occupied cells. On the retained witness that
changes both the intermediate endpoint pair and the final output.
