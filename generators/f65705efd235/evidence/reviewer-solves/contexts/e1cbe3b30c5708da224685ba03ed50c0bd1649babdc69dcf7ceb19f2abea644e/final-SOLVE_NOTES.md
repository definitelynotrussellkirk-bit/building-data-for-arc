# Solve notes

## Visible-example observations

1. Every nonzero color appears exactly four times.
2. The four cells of one color occupy two distinct rows and two distinct columns: they are the Cartesian-product corners of an axis-aligned rectangle.
3. The output begins from background 0 and adds the full perimeter of each inferred rectangle. Strict interiors remain 0 unless crossed by another rectangle border.
4. The two-cell-wide and two-cell-high cases are still rectangles: their adjacent sides become solid two-column or two-row strips.
5. Overlap order is observable in all three demonstrations. Where two inferred borders intersect, color 8 wins over 7, color 9 wins over 5, and color 5 wins over 2. The consistent hypothesis is ascending numeric paint order, so the larger color is visible at an intersection.

## Hypothesis implemented

For each nonzero color in ascending order:

- collect its cells;
- require exactly four cells forming all combinations of two rows and two columns;
- draw the top, bottom, left, and right edges of that rectangle on a fresh zero canvas.

This rejects accidental non-rectangular four-cell groups rather than inventing a bounding box for them. No reference implementation was consulted during this solve. I had seen the task rule earlier while reviewing the generator, so this is not claimed as a blind solve.
