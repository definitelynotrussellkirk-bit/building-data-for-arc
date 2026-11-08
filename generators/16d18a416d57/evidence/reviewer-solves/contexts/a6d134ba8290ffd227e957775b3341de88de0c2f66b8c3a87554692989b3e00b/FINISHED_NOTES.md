# Solve work log

## Prior exposure

Earlier rule exposure: **yes**. I had already inspected the assigned generator and
canonical behavior while repairing it. For this required solve episode I did not
consult the generator, Racket reference, private labels, or prior solution notes
after `prepare`; I used only the newly prepared visible examples.

## Revision 1

Visible pattern: every input contains separated 4-connected blue (`1`) objects.
In each demonstration exactly one object has the most cells. The output preserves
the grid and recolors every cell of that largest object orange (`7`). Its position
changes across the examples, and the largest object's size is 5 in examples 0 and
2 but 6 in example 1, ruling out a fixed-position or fixed-size interpretation.

Implementation: enumerate blue components with orthogonal flood fill, choose the
component with maximum cardinality, copy the input, and recolor that component to
7. Diagonal contact is not treated as connectivity. The visible examples show a
unique maximum; the implementation uses the first maximum only if an unseen tie
occurs, which is the remaining uncertainty.
