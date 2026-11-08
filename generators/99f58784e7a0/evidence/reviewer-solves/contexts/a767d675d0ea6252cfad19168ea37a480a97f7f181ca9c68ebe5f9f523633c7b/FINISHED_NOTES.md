# Solve notes

## Revision 1

The visible examples consistently use complete color-8 rows and columns as
walls.  Those walls split the remaining cells into 4-connected chambers.  Each
chamber contains exactly one nonzero/non-8 seed; every zero in that same chamber
is replaced by the seed color, while all 8 walls remain unchanged.

The second training example is decisive: its two bottom chambers both use color
7, so chamber identity—not global color uniqueness—controls the fill.  I
implemented the rule by finding every 4-connected component of cells that are
not 8, checking that it has one seed color, and painting the whole component.
This also handles the one-row-by-three-column and two-row-by-one-column layouts
shown in the visible data without hard-coding wall coordinates.
