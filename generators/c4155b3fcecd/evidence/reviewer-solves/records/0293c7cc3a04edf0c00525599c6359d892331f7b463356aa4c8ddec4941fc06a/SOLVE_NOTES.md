# Solve notes

## Visible-example observations

- Input and output shapes are unchanged.
- Every existing nonzero cell remains in place.
- For each nonzero cell at column `c`, the output also contains the same color at column `w - 1 - c` in the same row.
- The first training example is especially diagnostic because it has source cells on both sides: the color 6 at the far right creates a matching far-left 6, while left-side sources create right-side copies. This rules out a left-to-right-only rule.
- When both mirrored positions are already sources of the same color (the two 4s in training example 1), the output is simply their union; no cells are deleted.

## Hypothesis

Reflect every nonzero input cell across the vertical center line and union the reflected cells with the original grid. Center-column cells, if present, would map to themselves.

## Implementation

Scan the original input, not the progressively modified output, and write each nonzero value to its horizontal mirror in a copied grid. This avoids accidental cascading and preserves all sources.
