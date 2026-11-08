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

## Revision 2 — preserve the template's actual crossing colors

The first revision produced the right shapes but failed all three visible
examples. A cell-by-cell comparison localized every mismatch to intersections
between a special horizontal fill row and persistent marker columns. I had
incorrectly assumed vertical marker colors always win at crossings.

The colored template itself specifies the crossing color. For example, an
all-7 special row overwrites every persistent marker at that row, while a
mostly-3 row may retain the 6 marker at one crossing and overwrite the others.
The revised program therefore obtains ordinary marker colors from a base row,
but for every special row it copies that row's actual values at marker columns
after filling the remaining output cells. No panel parsing or row pairing was
changed.
