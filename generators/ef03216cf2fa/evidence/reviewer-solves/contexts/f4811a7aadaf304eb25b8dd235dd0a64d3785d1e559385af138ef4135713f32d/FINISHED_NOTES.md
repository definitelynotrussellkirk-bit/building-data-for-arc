# Exposed visible-only solve notes

Earlier rule exposure: yes, from the generator review. During this solve I did
not reopen the generator, canonical rule, private labels, or prior solution text.

From the three visible examples:

1. Each nonzero monochrome 4-connected object is handled separately and cropped
to its tight bounding box.
2. A crop taller than wide is rotated 90 degrees clockwise. Example 0's color-2
4x3 crop becomes the first 3x4 block, and example 2's color-3 4x2 crop becomes
2x4. The asymmetric examples determine the direction.
3. Objects are ordered by bounding-box perimeter descending. Equal perimeters
would retain input row-major order.
4. Crops are placed left-aligned in one output, top-to-bottom, with one all-zero
row between consecutive crops. Output width is the maximum post-rotation crop
width and output height is the sum of crop heights plus the separators.

The implementation independently extracts same-color 4-connected components,
applies that transformation, and does not mutate the input.
