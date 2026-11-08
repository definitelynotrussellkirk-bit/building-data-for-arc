# Solve work log

## Exposure

Before this solve I had not opened this task's generator, Racket rule, reference
solution, private query labels, audit records, or earlier solution explanation.
I used only the visible examples prepared in this directory.

## Revision 1 — complete three-corner rectangles

Each nonzero color appears exactly three times. In every training example, the
three cells of one color occupy three corners of an axis-aligned rectangle: there
are exactly two used row indices and two used column indices. The output preserves
the input and paints the fourth Cartesian-product corner with the same color.
This explains every added cell and every unchanged cell across all three examples,
including multiple independent colors in one grid.

The implementation groups nonzero cells by color, requires three cells spanning
two rows and two columns, finds the one absent row/column combination, and fills
it. It deliberately leaves malformed groups unchanged rather than guessing.

Remaining uncertainty is limited to whether hidden inputs include malformed color
groups; the visible task consistently presents independent three-corner rectangles,
so conservative no-op behavior is preferable outside that pattern.
