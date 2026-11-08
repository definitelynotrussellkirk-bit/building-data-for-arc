# Solve notes

Human work log based only on the prepared visible examples.

- All examples preserve grid size and background 0.
- Each nonzero 4-connected block is a solid monochrome rectangle.
- Strict interior cells are cleared while the bounding-box perimeter remains.
- Example 0 is decisive for grouping: color 1 occurs in two disconnected rectangles, so each connected object must be processed independently rather than taking one global box per color.
- Two-cell-wide or two-cell-high rectangles have no strict interior and therefore remain unchanged.
- Implemented a generic same-color 4-connected component scan followed by painting each component's bounding-box perimeter into a fresh zero grid.
