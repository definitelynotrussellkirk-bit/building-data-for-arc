# Post-repair visible-example solve notes

This is not a blind solve: I had already inspected the selected rule while repairing the generator. During this solve episode I used only `solve/challenge.json` and did not reopen the generator, Racket source, canonical solution, private labels, or earlier solution explanations.

## Hypothesis

The full-height column of 9s is a vertical reflection axis. Preserve the entire input. For every nonzero, non-9 cell strictly left of that axis, place the same color in the equal-distance cell on the right: `(r, c) -> (r, 2*axis-c)`.

## Visible-example checks

- Training example 0: column-0 color-1 cells with axis 4 land at column 8, matching all three output additions.
- Training example 1: with axis 5, column 0 maps to 10 and column 1 maps to 9; the multicolor row `[4,8]` appears as `[8,4]` on the right, ruling out translation without reflection and ruling out recoloring.
- Training example 3: the mixed-color connected shape is copied cell-for-cell and color-for-color; no original cell is removed.

No competing rule survived these checks, so I wrote one implementation revision. It locates the unique full 9-column, copies the grid, and mirrors every left-side non-background/non-divider cell when the target is in bounds.
