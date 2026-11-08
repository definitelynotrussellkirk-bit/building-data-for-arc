# Solve work log

## Prior exposure declaration

Before this visible-only episode I had already inspected this task's generator and
canonical authority while repairing it. I therefore cannot call this a blind solve.
After `prepare`, I did not reopen the generator, Racket rule, reference solutions,
or private query labels; the program below was checked only against the three
visible input/output pairs.

## Revision 1

All three examples preserve the input shape, erase every nonzero object, and leave
one cell of the object's original color. I treated an object as a 4-connected
same-color component. The retained cell lies at the floor midpoint of the tight
bounding box: `((min_row + max_row) // 2, (min_col + max_col) // 2)`.

The repeated colors in examples 1 and 2 are important: disconnected objects of
the same color each produce their own cell, so grouping globally by color is not
adequate. Example 1 also contains a 2-by-4 component whose output selects the
lower-index midpoint, distinguishing floor midpoint from the upper midpoint and
from a rounded cell centroid.

Implementation: scan all cells, flood-fill each unseen nonzero same-color
component, compute its bounding box, and write exactly one colored cell into a
zero-filled output grid. I expect this to handle both visible queries without any
special casing. Remaining uncertainty is limited to object connectivity; the
visible examples support 4-connectivity rather than diagonal merging.
