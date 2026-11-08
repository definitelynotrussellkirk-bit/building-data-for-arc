# Visible-only solve notes

## Hypothesis

Treat each nonzero same-color 4-connected component separately, including disconnected components that reuse a color. Replace each component by one cell of its color at the floor midpoint of its tight bounding box; clear every other cell.

## Evidence from the displayed examples

- Train 0: the vertical color-8 bar spanning rows 2..4 maps to `(3,1)`; the 3x3 color-7 block at rows 2..4, columns 7..9 maps to `(3,8)`; the horizontal color-6 bar maps to `(6,6)`.
- Train 1: two disconnected color-2 objects produce two output cells, so the unit is a connected component, not an entire color class. The hollow 3x3 color-2 ring maps to its blank bbox center `(5,4)`, so the chosen position need not be occupied in the input.
- Train 1's asymmetric 2x4 color-4 object maps to floor bbox midpoint `(1,6)`, not the rounded cell centroid or the upper/ceiling bbox midpoint.
- All outputs preserve input dimensions and erase the source objects.

## Implementation choice

Use 4-neighbor flood fill by exact color, compute each component's min/max row and column, and paint `((r_min+r_max)//2, (c_min+c_max)//2)` on a fresh zero grid.
