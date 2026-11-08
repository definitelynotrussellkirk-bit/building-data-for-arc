# Solve notes

This is an exposed post-repair solve. I had already seen the task family during
generator review, so this is not blind; during this solve phase I used only the
visible prepared examples and did not reopen a reference rule or generator.

Visible-example hypothesis:

1. Each input contains three monochrome 4-connected shapes.
2. Order the shapes by their leftmost input column, not by source color. Example
   1 is especially useful because its left-to-right colors are 7,2,5.
3. Crop each shape to its bounding box and replace its color by a binary mask.
4. Top-left-pad all masks to the largest height and width (3×3 in the examples).
5. Form a 3×3 ordered matrix. Cell `(i,j)` is the binary OR of masks `i` and `j`,
   rendered in color 8. Put one all-zero row and column between adjacent panels.

The diagonal panels reproduce the individual masks; symmetry across the panel
matrix follows because OR is commutative. The implementation is generic in the
number and common dimensions of the shapes even though the visible task uses
three 3×3-normalized masks.
