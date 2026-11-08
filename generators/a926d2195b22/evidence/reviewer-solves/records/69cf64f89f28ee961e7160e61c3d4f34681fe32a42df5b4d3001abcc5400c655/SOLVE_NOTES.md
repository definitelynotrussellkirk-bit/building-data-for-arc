# Solve notes

I used only the newly prepared visible examples while solving this final-source episode. I had already seen the task's rule during the repair, so the final exposure declaration is `yes`; I did not consult the Racket/reference implementation during this solve.

## Hypothesis

Treat every nonzero monochromatic 4-connected region as an object. Recolor the object with the fewest cells to 9 and preserve everything else. If several objects share the minimum size, choose the one whose first occupied cell appears earliest in row-major order.

## Visible evidence

- Example 0 contains singleton components at `(2,7)` and `(7,2)`. Only the earlier singleton at `(2,7)` changes, ruling out both “all minima” and a color-wide replacement.
- Example 1 contains a size-3 color-8 component, a separate singleton color-8 component at `(4,9)`, and a size-4 color-7 component. Only the singleton changes, so connected-component size—not global color frequency—is decisive.
- Example 2 contains singleton components at `(0,0)` and `(6,8)`. The earlier one changes, confirming the row-major tie policy.

## Implementation

Scan cells in row-major order, flood-fill equal-color 4-neighbors, rank components by `(cell_count, first_row_major_cell)`, deep-copy the grid, and recolor the selected component to 9.
