# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, canonical rule, notes, reference solution,
audit material, or private query labels. I used only the visible presentation
printed by `python3 review.py blind prepare` and the files in `solve-blind/`.

## Revision 1 — row-confinement hypothesis

The transformation preserves every nonzero color whose occurrences all lie in
one horizontal row, and replaces every nonzero color occurring in two or more
rows with background 0. Singleton colors are therefore retained automatically.

Evidence from the visible examples:

- Example 0 keeps color 1 (all four cells in row 0) and singleton color 4,
  while color 3 spans rows 3, 4, and 6 and is erased.
- Example 1 keeps color 1 (all in row 2) and singleton color 5. Colors 2 and 7
  span multiple rows and are erased.
- Example 2 keeps colors 5 and 3 (each confined to one row) plus singleton
  colors 9 and 7. Colors 6, 1, and 2 each span multiple rows and are erased.

An early visual alternative was that singleton colors might point to a color to
preserve. Example 2 argues against that: singleton 7 is directly below a color-1
cell, yet color 1 is erased. Row confinement explains all examples without a
special marker role.

Predicted query behavior:

- Query 0 keeps colors 1, 4, and 2; color 6 is erased because it spans rows 1,
  4, and 5.
- Query 1 keeps colors 4, 3, 7, and 8; colors 9, 1, and 6 are erased because
  each appears in multiple rows.

Implementation records the row set for each nonzero color and keeps exactly
those with row-set size one. Remaining uncertainty is low; the visible examples
do not test a nonzero color absent from a grid (irrelevant) or a nonzero color
occupying every column of one row (still covered by the same rule).
