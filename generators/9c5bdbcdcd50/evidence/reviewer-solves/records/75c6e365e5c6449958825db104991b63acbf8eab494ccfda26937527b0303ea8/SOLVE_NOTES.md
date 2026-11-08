# Solve work log

I had no known earlier exposure to task `9c5bdbcdcd50` and did not consult its
Racket rule, generator, reference solutions, private labels, prior notes, or audit
records. I used only the visible examples prepared in this directory.

## Revision 1 — outermost separator rectangle

The input is a rectangular lattice made from complete color-3 rows and columns.
The output preserves every separator line. The first and last complete rows and
columns delimit an outer rectangle:

- zero cells strictly inside both pairs of outermost lines become color 7;
- the exterior top-left and top-right corner rectangles become 2 and 4;
- the exterior bottom-left and bottom-right corner rectangles become 1 and 8;
- exterior side strips that are not in a corner, and separator cells, stay as-is.

This matches all three visible examples. For example, train 2 has outermost
separator rows 2 and 8 and columns 1 and 9. Thus rows 3–7 and columns 2–8 are
the interior (with internal separator row 4 and column 3 preserved), while the
four nonempty corner regions receive 2, 4, 1, and 8. Train 0 confirms that the
sizes of the corner rectangles can differ independently.

I implemented the rule by detecting complete nonzero rows/columns, inferring the
common separator color, then recoloring only background-zero cells. Remaining
uncertainty: the visible data always uses zero as background and has at least two
complete separator rows and columns. The implementation returns an unchanged
copy when that structure is absent rather than guessing.
