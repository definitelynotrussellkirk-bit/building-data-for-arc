# Post-repair visible-example solve notes

## Observation

Each input contains several isolated, single-color, 4-connected nonzero objects on a zero background. The output side length equals the number of objects: three objects produce a 3×3 matrix and four objects produce a 4×4 matrix.

The diagonal is always 1. Comparing object cell counts explains the off-diagonal entries:

- train 0 has row-major/bounding-top-left object sizes 4, 2, 4 and output rows `[1,2,1]`, `[3,1,3]`, `[1,2,1]`;
- train 1 has object sizes 7, 2, 5 when ordered by bounding-box top-left, and the 7-cell object is encountered by a naïve row scan only after the 2-cell object. The output nevertheless begins with the 7-cell object, so order is not component-discovery order;
- train 2 includes equal 4-cell objects in positions 1 and 4, producing symmetric off-diagonal 1s;
- train 3 again places an object whose uppermost cell begins to the right of another object's first visible cell, confirming that ordering uses the object's bounding-box top-left coordinate (top row, then left column).

## Hypothesis

1. Extract each nonzero same-color 4-connected component.
2. Sort components by `(minimum row, minimum column)`.
3. Let their cell counts be `a[i]`.
4. Return an N×N matrix with 1 for equality, 2 when `a[i] > a[j]`, and 3 when `a[i] < a[j]`.

Colors identify components but do not determine matrix values. Cell count, not bounding-box area, is the compared quantity.

## Implementation

The solver performs a breadth-first flood fill for each nonzero component, records its bounding-box top-left and cell count, sorts those records, and builds the pairwise comparison matrix. I stopped after one revision because the hypothesis accounts for every visible cell of all four training outputs and directly handles both five-object queries.
