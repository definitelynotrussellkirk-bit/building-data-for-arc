# Solve notes

## Hypothesis

Each input contains one filled two-color rectangle and one cyan marker (`8`) outside it, aligned with a row or column of the rectangle. The output expands the rectangle's bounding box just far enough to include the marker. The original perimeter color becomes the perimeter of the expanded rectangle, the original interior color fills its strict interior, the cyan marker disappears, and all cells outside the expanded rectangle are zero.

## Evidence from the visible examples

- Example 0: the cyan marker is above the rectangle at the rectangle's left edge; the output extends the rectangle upward to that row, preserving frame color 6 and interior color 5.
- Example 1: the marker is above the rectangle on its left frame column; the same vertical expansion occurs with frame color 6 and interior color 4.
- Example 2: the marker is left of the rectangle on an interior row; the output extends leftward to the marker, using frame color 1 around the enlarged box and interior color 6 inside.

## Implementation plan

1. Locate the first cyan cell.
2. Collect all nonzero, non-cyan cells and take their bounding box.
3. Read the frame color from the original top-left corner and the interior color as the other rectangle color (falling back to the frame color for robustness).
4. Union the rectangle bounds with the cyan coordinate.
5. Rebuild the grid from zeros, coloring the new perimeter with the frame color and the strict interior with the interior color.

This is a direct visible-example hypothesis; no generator, Racket rule, reference answer, or private query label was consulted during this solve phase.
