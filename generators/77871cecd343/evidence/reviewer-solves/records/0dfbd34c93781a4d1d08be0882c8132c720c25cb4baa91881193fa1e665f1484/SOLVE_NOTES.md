# Solve work log

## Prior exposure

I had already inspected this task's rule and generator before this required final solve, so earlier rule exposure is **yes**. During this solve I kept the generator, Racket source, private labels, prior solve, and reference solutions closed. I used only `solve/challenge.json` and visible check feedback.

## Revision 1

### Visible pattern

Every example contains exactly one complete row and one complete column of color 9. Their intersection is the reflection center. A connected color-1 shape appears in one of the four regions separated by that cross. The output preserves the original color-1 shape and the color-9 cross, then creates color-8 copies at the horizontal reflection, vertical reflection, and double reflection of every color-1 cell.

The cross is not always at the geometric center of the rectangular canvas, so the implementation detects the all-9 row and all-9 column directly rather than using `height // 2` and `width // 2`.

### Implementation

1. Find the unique full color-9 row and column.
2. Collect the original color-1 coordinates.
3. Copy the grid.
4. For each source cell `(r, c)`, paint 8 at `(r, 2*axis_col-c)`, `(2*axis_row-r, c)`, and `(2*axis_row-r, 2*axis_col-c)` whenever the destination is background.
5. Preserve existing 1 and 9 cells.

### Remaining uncertainty before checking

The visible examples consistently keep the original object color 1 and use color 8 only for the three reflected copies. No visible example requires collision handling beyond preserving nonzero cells, and all reflected coordinates remain in bounds.
