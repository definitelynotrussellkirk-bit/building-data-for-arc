# Solve work log

## Prior exposure

This is not a blind solve. Before preparation I had already read and repaired the
assigned generator and had seen the canonical rule. During this solve I did not
reopen the generator, Racket source, reference outputs, private labels, or prior
solution explanations. I used only the visible examples printed by `solve
prepare` to confirm the program.

## Revision 1 — fill aligned pair midpoints

In each visible example, every nonzero color occurs exactly twice. When its two
cells share a row or column, the output adds one cell of that color at their
integer midpoint while preserving all input cells. Example 1 confirms both a
vertical color-4 pair and a horizontal color-1 pair; example 2 confirms that the
operation is applied independently to three colors.

The program groups coordinates by color, requires exactly two cells, checks
row/column alignment and an integral midpoint, and fills that midpoint only when
it was background in the input. For query 0 this adds color 5 at `(1,0)`. For
query 1 it adds color 8 at `(1,4)`, color 3 at `(3,2)`, and color 2 at `(2,6)`.
The visible examples do not test odd spans, obstructed midpoints, or colors with
other multiplicities, so the implementation leaves those cases unchanged.
