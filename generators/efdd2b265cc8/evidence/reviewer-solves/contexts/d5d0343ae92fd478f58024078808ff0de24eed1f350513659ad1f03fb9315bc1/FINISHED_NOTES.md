# Solve notes

The visible demonstrations preserve every color and cell count while swapping
coordinates `(row, column)` to `(column, row)`.

- Example 1 moves color 3 from `(1, 0)` to `(0, 1)`, color 7 from `(3, 0)` to
  `(0, 3)`, and color 4 from `(2, 3)` to `(3, 2)`.
- Example 0 maps the vertical color-6 triad in column 4 to a horizontal triad in
  row 4, while the color-1 L-shape is transposed independently.
- Example 2 maps the 2x2 block at rows 2-3, columns 0-1 to rows 0-1, columns
  2-3; the diagonal singleton remains fixed.

Hypothesis: transpose the whole input across the main diagonal. Python's
`zip(*grid)` implements the coordinate swap and also handles rectangular grids
shape-safely, although every displayed instance here is square.

This is a human work log. I had earlier rule exposure from reviewing this same
generator, so the episode is not blind. During this solve phase I used only the
visible examples and did not reopen the generator, Racket rule, reference
solutions, or private labels.
