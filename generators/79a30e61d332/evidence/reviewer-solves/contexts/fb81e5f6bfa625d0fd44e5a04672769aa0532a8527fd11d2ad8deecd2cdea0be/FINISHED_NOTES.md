# Solve notes

The grids are a 4×6 lattice of 3×3 symbols separated by zero rows and columns. The one symbol drawn in color 8 is a template. In every training pair, each tile with the exact same occupied-cell pattern becomes color 8, regardless of its original color. For each pair of matching tiles sharing a tile row or tile column, the nonzero cells of every intervening tile become color 7. Other cells remain unchanged.

I checked exact cell-pattern equality rather than only tile population or per-row totals: the examples contain visually similar distractors that remain color 1. I also use all matching tiles, including bridges not incident to the originally color-8 tile.

This is an exposed solve: I had already inspected the task rule during generator repair. During this solve episode I used only the visible challenge presentation and did not reopen the generator, Racket rule, canonical record, or private answers.
