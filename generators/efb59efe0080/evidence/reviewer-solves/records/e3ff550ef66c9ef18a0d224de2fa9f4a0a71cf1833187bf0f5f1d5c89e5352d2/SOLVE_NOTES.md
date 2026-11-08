# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, reference solution, private
query labels, audit evidence, or earlier solution notes. I used only the visible
examples produced by `python3 review.py blind prepare` and the files in
`WORK/solve-blind/`.

## Revision 1 — normalized silhouette XOR

Each input contains one red (`2`) object and one green (`3`) object. I cropped
both objects to their own bounding boxes and compared the resulting occupancy
masks with their top-left corners aligned. In all three demonstrations, the
output is exactly the cells occupied by one mask but not both (symmetric
difference/XOR), recolored azure (`8`), followed by removal of all-empty outer
rows and columns.

Checks by hand:

- Example 1's two 3×3 masks XOR directly to the shown 3×3 output.
- Example 0's XOR has content only in its first column, explaining the 3×1 crop.
- Example 2's XOR has an empty first column, explaining the shown 3×2 crop.

The implementation permits unequal object bounding boxes by padding missing
cells as empty, then crops the XOR result. Remaining uncertainty is the fully
overlapping case; no visible example defines its output, so the implementation
returns a single background cell rather than an empty/ragged grid.
