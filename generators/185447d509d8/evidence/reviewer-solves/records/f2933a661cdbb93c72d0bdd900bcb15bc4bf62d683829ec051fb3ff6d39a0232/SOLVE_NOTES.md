# Solve work log

## Prior exposure

I had already inspected this task's generator and canonical behavior while repairing it, so this is **not blind**. During this solve phase I did not reopen the generator, Racket rule, reference solution, private query labels, or prior solution explanations. I used only the newly prepared visible examples and my own implementation.

## Visible-example inference

Each input contains four isolated monochrome objects, and each output is a 4x4 symmetric matrix using 2 and 0. The diagonal is always 2. The examples imply that rows and columns correspond to objects ordered by the row-major position of their bounding boxes.

The off-diagonal 2s group objects by binary shape while ignoring color, translation, rotation, and reflection:

- Train 0 pairs the top-left S/Z-like object with the bottom-right reflected form, and pairs the two straight tetrominoes despite a 90-degree rotation.
- Train 1 pairs the two straight tetrominoes and separately pairs the two reflected/rotated skew tetrominoes.
- Train 2 has the same two-pair matrix pattern with different placements and colors.

A same-cell-count rule is ruled out because all four objects have four cells but the matrix contains zeroes. An exact-orientation rule is ruled out by rotated straight bars. A rotations-only rule is ruled out by the reflected skew pair.

## Implementation

1. Extract nonzero same-color 4-connected components.
2. Sort components by `(minimum row, minimum column)` of each bounding box.
3. Normalize every component to its local top-left origin.
4. Enumerate four rotations and their left-right reflections.
5. Emit 2 when the column shape is in the row shape's eight dihedral forms, otherwise 0.

No failed code revision was needed; the three examples jointly determine the tested relation clearly. Remaining uncertainty is only whether object ordering uses the bounding-box top-left versus another equivalent row-major locator. The visible layouts make these agree, and bounding-box order is the most natural stable interpretation.
