# Solve notes — 78143e5d7ed1

## Visible-example hypothesis

Each input contains three or four isolated monochrome 4-connected objects. The output preserves each object's tight bounding-box crop, including zero holes inside that crop, and concatenates the crops horizontally with one all-zero separator column.

The crops are bottom-aligned to the tallest crop. Their left-to-right order is ascending lexicographic order of:

1. foreground cell count,
2. bounding-box height,
3. bounding-box width,
4. numeric color.

Evidence from the visible examples:

- Example 0 places the 5-cell color-4 crop before two 6-cell crops; among the two area-6 crops, the 2-row color-3 rectangle precedes the 3-row color-2 rectangle, showing area then height.
- Example 2 places area-5 color 4 first; the two area-6, height-3 crops are ordered width 2 before width 3, showing the width tie-break.
- Examples 1 and 3 contain equal area/height/width shapes whose order follows color, showing the final tie-break.
- Unequal crop heights are consistently bottom-aligned, and sparse cells inside each tight bounding box remain zero rather than being filled.

## Implementation plan

Scan row-major, flood-fill each same-color component with 4-neighbor connectivity, compute its tight box and crop, sort by the tuple above, allocate the packed output, and copy each crop at `max_height - crop_height`.
