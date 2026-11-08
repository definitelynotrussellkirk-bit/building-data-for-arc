# Visible-only solve notes

This is a human-authored work log. I had earlier exposure to the generator family during the repair, so this is not a blind solve; while solving I used only the prepared visible examples and did not reopen the generator, Racket rule, reference solution, or private labels.

## Hypothesis

Across all four demonstrations, cyan (`8`) cells act as sparse boundary markers for an axis-aligned rectangle. The only changed cells are blue (`1`) cells whose coordinates lie inside the smallest rectangle containing every cyan cell; those blue cells become green (`3`). Cyan, background, and blue outside that rectangle are preserved.

The examples distinguish this from recolouring every non-cyan cell in the rectangle: some internal zeros remain zero. They also distinguish using only adjacency to cyan because changed blue cells can be separated from cyan markers.

## Implementation

1. Collect all cyan coordinates.
2. Compute their minimum and maximum row and column.
3. Copy the grid.
4. Within that inclusive bounding box, replace only value `1` with `3`.
5. Return the copy; if no cyan exists, conservatively return an unchanged copy.

No diagnostic or intentionally wrong revisions were used.
