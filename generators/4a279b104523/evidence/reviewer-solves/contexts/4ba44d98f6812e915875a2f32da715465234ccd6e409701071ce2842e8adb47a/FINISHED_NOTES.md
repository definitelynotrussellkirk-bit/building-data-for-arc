# Solve notes

## Visible evidence

All three demonstrations contain exactly one complete horizontal row of color 8. The output preserves that row and every pre-existing colored cell. For each other colored cell at row `r`, column `c`, a same-colored cell appears at the same column on the opposite side of the 8-row, at row `2*axis-r`.

The demonstrations deliberately cover both directions:

- Train 0 has sources above the axis and adds copies below.
- Train 1 has sources below the axis and adds copies above.
- Train 2 mixes a source above with sources below and completes both directions.

This rejects an “above-only” copy rule. The third example also places the 8-row away from the geometric center, so the axis must be the marked row rather than the grid midpoint.

## Revision 1 hypothesis

Find the unique full color-8 row. Preserve the input. Reflect every nonzero, non-8 cell vertically through that row in the same column. Write the copy only when its reflected row is inside the canvas; this is the natural boundary behavior and avoids indexing outside the grid.

Implementation includes structural checks for a unique full 8-row and otherwise applies the geometry directly.
