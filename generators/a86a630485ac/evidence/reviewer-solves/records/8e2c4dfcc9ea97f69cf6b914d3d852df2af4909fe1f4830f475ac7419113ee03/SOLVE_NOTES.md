# Blind solve notes — a86a630485ac

This is a human visible-example work log. I did not inspect the generator,
canonical rule, private labels, prior solutions, or audit records.

## Observations

Each grid contains three separated colored objects on a black background. The
output deletes whole objects rather than moving or recoloring cells.

- Train 1 keeps the color-2 cross and the width-1 color-5 bar, but removes the
  asymmetric color-6 L.
- Train 2 keeps color 8. Its rows are `0110 / 0110 / 1111`, symmetric under a
  left-right reflection of its bounding box. The color-1 skew tetromino and
  color-2 `1100 / 1111 / 1100` object are not left-right symmetric.
- Train 3 keeps color 5 (`010 / 010 / 111`) and removes the right-heavy color-9
  and skew color-4 objects.

This rules out simple size selection: Train 1 keeps sizes 5 and 2 while deleting
size 4, and Train 2 deletes one of the two size-8 objects. The shared property is
vertical-axis (left-right) symmetry inside each object's own bounding box.

## Hypothesis and implementation

Split nonzero cells into same-color 4-connected components. Preserve a component
iff reflecting every occupied cell through the vertical axis of its bounding box
lands on another occupied cell in that component. Replace all other cells with 0.

Predictions:

- Test 1 keeps only color 9. Color 9 is `0110 / 0110 / 1111`; colors 2 and 7
  are left-aligned/right-aligned asymmetric shapes.
- Test 2 keeps colors 1 and 2. The color-1 diamond and color-2
  `111 / 010 / 010` are left-right symmetric; color 7 is `100 / 111 / 100`.

No alternative remained consistent with all three demonstrations after the size
counterexample comparison, so I made one solve attempt rather than manufacturing
an artificial failed revision.
