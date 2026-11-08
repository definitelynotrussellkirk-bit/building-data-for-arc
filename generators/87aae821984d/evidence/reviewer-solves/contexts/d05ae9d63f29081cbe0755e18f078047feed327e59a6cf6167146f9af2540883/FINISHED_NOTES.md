# Solve notes

This is a human work log from the visible examples only. I had earlier rule exposure from repairing the generator, so this is not a blind solve; I did not consult the generator, Racket source, reference solution, private labels, or prior solve files during this episode.

## Hypothesis

The number of yellow `4` cells controls horizontal repetitions. The cyan `8` cells are treated as one motif even when disconnected. The motif is embedded in a fixed 3×3 tile by aligning its tight bounding box to the tile's bottom-right, which means any missing row/column is padded on top/left. Repeat that 3×3 tile once per yellow cell.

Evidence from the three demonstrations:

- Example 0 has one yellow cell and a 3×3 cyan span, producing one 3×3 tile.
- Example 1 has two yellow cells and a 2×3 cyan bounding box; its output adds a blank top row and repeats twice.
- Example 2 has three yellow cells and a disconnected 3×2 cyan bounding box; its output adds a blank left column and repeats three times.

## Implementation

Collect all cyan coordinates, use the maximum row and column as the tile's bottom-right anchor, reconstruct the preceding 3×3 window, and multiply each tile row by the count of yellow cells.
