# Solve notes

The visible examples suggest a per-color rule on a background-0 grid:

1. Scan colors by their first visible occurrence in row-major order.
2. A color is active only when it occurs exactly twice and its two cells are in different rows and different columns.
3. Treat those cells as opposite corners and paint the full perimeter of their bounding box in that color.
4. Leave singletons, same-row/same-column pairs, and colors occurring three or more times unchanged.
5. Apply active colors sequentially, so a later outline may overwrite an earlier outline or a decoy cell.

Checks against the visible examples: exact diagonal pairs expand; the aligned color-8/color-2 examples and 3-cell colors remain as markers; intersecting boxes use scan-order overwrite behavior. The implementation copies the input and never mutates the caller's grid.
