# Visible-only solve notes

I inspected only `solve/challenge.json` after preparation. I had earlier exposure
to the task while repairing its generator, so this is intentionally recorded as
an exposed post-repair solve, not a blind solve. I did not consult the generator,
Racket authority, reference solutions, private labels, or the archived earlier
solve during this episode.

## Hypothesis

Across the three visible pairs, color 3 forms sparse V/chevron outlines on top
of irrelevant 0/1 texture. The output preserves every marker and paints color 8
through the triangular wedge bounded by each outline. Chevrons may point up,
down, left, or right; arm markers may have one-cell gaps; multiple wedges are
unioned; and painting clips at the grid boundary.

## Implementation

1. Group color-3 markers when they are at Chebyshev distance at most two and
   share a row, column, or diagonal.
2. For each group, search marker cells as candidate apices and the four cardinal
   pointing directions. A valid sparse chevron places every marker on one of
   the two diagonal rays and has evidence on both arms.
3. Use the farthest marker as depth, fill each cross-section of the wedge with
   color 8, clip to bounds, and never overwrite color-3 markers.

The first submitted revision is the generic decoder above; no deliberate wrong
teaching example was added.
