# Solve notes

This is a human-readable work log based only on the newly prepared visible examples. I had already seen the task rule while reviewing the generator, so this is an exposed post-repair solve, not a blind solve. During this solve phase I did not consult the generator, Racket source, reference solutions, private labels, or the archived earlier solve.

## Visible-example hypothesis

Treat each column containing nonzero cells independently. If a column contains `k²` colored cells, move those cells into a bottom-aligned pyramid centered on that same column. From bottom to top, the pyramid widths are `2k-1, 2k-3, ..., 1`.

The source row gaps disappear. Reading source colors from bottom to top gives the bottom-to-top color order in the pyramid. A color keeps its total count and therefore fills one or more whole adjacent pyramid layers. Examples with counts `5,3,1` give three differently colored layers; counts `5,4` give one bottom color and one color across the upper `3+1` cells. Multiple active columns are transformed independently.

## Probe implemented

The solver preserves the canvas dimensions, checks that every active column has a square number of cells, allocates each color count to complete pyramid layers in bottom-to-top order, and paints those layers at the bottom of the original column.
