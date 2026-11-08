# Visible-only solve notes

The first row is a legend: its contiguous nonzero cells are output colors in rank order. The remaining nonzero cells form cardinally connected components. Across the examples, component area—not top-left position—determines the primary ordering: largest gets the first legend color, next-largest the second, and so on. Example 0 also shows an equal-area pair; the upper/left component receives the earlier legend color, so ties use top row and then left column. A legend entry may be 8, in which case that ranked component remains color 8.

Implementation: preserve the grid and header, flood-fill all nonzero components below row 0, sort by `(-area, min_row, min_col)`, and repaint with the legend in order.
