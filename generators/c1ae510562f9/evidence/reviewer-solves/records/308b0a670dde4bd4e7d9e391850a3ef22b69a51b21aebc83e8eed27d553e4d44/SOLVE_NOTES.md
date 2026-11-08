# Solve work log

## Exposure before solving

I had not opened this task's generator, Racket rule, reference outputs, private labels,
audit evidence, or any selected repair source. I used only the visible presentation
produced by `python3 review.py blind prepare` and `challenge.json`.

## Revision 1 — empty interior rows become a 3×3 spiral prefix

The outputs are prefixes of one clockwise 3×3 spiral order: top-left, across the top,
down the right, across the bottom, up the left, then center. Their prefix lengths are
4, 8, 9, and 8.

For each input, I treated the gray 5 cells as an open-top U. The relevant interior rows
run from the first row containing both vertical walls through the row immediately above
the gray bottom bar. Counting rows with **no cyan 8 cell between the walls** gives 4,
8, 10, and 8; capping at the nine output cells exactly gives the four visible outputs.
This also predicts query prefix lengths 4 and 8.

I considered total cyan count, filled-area fraction, connected components, and coarse
resizing of the U, but each contradicted at least one visible pair (especially the two
examples with only four cyan cells but eight output cells). The empty-row count is the
only simple invariant I found that matches every pair and explains why multiple cyan
cells in one row still contribute a single occupied row.

The implementation finds the bottom as the row with the longest horizontal gray bar,
uses its extreme gray columns as the walls, finds their first common row, counts empty
interior rows, and paints the capped clockwise spiral prefix.

Remaining uncertainty: the visible data does not show malformed U shapes, alternate
colors, unequal wall starts, or ties for the longest gray row. I intentionally did not
add behavior for unsupported structures.
