# Solve notes

## Visible-example observations

- In each demonstration, gray (`5`) cells occupy two columns and establish a rectangular bounding box even when the side markers are sparse or gapped.
- The output uses the gray box's leftmost and rightmost columns exactly; it does **not** add a horizontal halo.
- Vertically, the output begins one row above the first gray row and ends one row below the last gray row.
- Blue (`8`) cells outside that crop are discarded, while blue cells in either halo row and inside the gray columns are preserved unchanged.

## Hypotheses considered

1. **Bounding box of every nonzero cell.** Rejected: each input has blue distractors well outside the output.
2. **Crop only the gray bounding box.** Rejected: every output has two more rows than the gray row span, one above and one below.
3. **Find a continuous gray-sided rectangle.** Rejected: the second demonstration uses only corner-like/gapped gray markers but follows the same crop.
4. **Gray bounding-box columns plus a one-row vertical halo.** Fits all three visible demonstrations exactly and explains the retained/discarded blue cells.

## Implementation

Collect all coordinates whose value is `5`, compute their min/max row and column, and slice rows `min_row - 1` through `max_row + 1` inclusive and columns `min_col` through `max_col` inclusive. The source examples guarantee the vertical halo exists; the implementation raises clearly if it does not.
