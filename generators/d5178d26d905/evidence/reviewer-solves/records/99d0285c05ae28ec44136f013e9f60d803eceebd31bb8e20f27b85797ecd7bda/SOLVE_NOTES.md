# Solve work log

## Exposure

I previously reviewed this generator and therefore had earlier exposure to its
intended transformation. During this separate solve I did not reopen the
Racket rule, generator source, reference solutions, private labels, or earlier
solution explanations. I used only the visible examples printed by `solve
prepare` and my own implementation.

## Revision 1 — transfer the colored template into the 0/4 reference geometry

Each input has two panels separated by a full vertical line of color 5. One
panel contains only 0 and 4 and determines the output geometry. The other has a
colored template, sometimes above or below rows of 5 padding.

In the 0/4 panel, intersecting the sets of 4-columns across all marked rows
finds persistent marker columns. Rows with additional 4s are special rows. In
the colored panel, intersecting nonzero columns across all active rows finds
the corresponding persistent marker columns and their colors. Rows with
nonzero values outside those columns are special rows, each carrying one fill
color.

The output has the reference panel's dimensions. Persistent colored markers are
placed in the persistent reference columns on every row. Special template rows
and special reference rows are paired top-to-bottom; each special reference row
is filled with that template row's fill color everywhere except the persistent
marker columns.

This explains both panel orders in the visible data. For query 0 the reference
is left of the divider and has marker columns 4 and 5; its two special rows take
fill colors 9 and 8. For query 1 the reference is right of the divider and has
marker columns 2, 6, and 7; its three special rows take fill colors 3, 1, and 2.

Remaining uncertainty: the visible examples only use a vertical divider, so the
program intentionally implements that demonstrated orientation rather than
inventing an unsupported horizontal variant.
