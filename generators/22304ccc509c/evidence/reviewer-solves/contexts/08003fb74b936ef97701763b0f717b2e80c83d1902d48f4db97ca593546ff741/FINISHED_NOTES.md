# Visible-only solve notes

The three demonstrations preserve the grid dimensions, the set and counts of colors,
and each nonzero cell's column.  Within every column, the nonzero sequence is packed
against the bottom while retaining its original top-to-bottom order.  Example 0 is
the key order check: column 0 keeps `4,6,3`; column 5 keeps `5,9,1`.  Therefore this
is not color sorting and not movement toward a global object.

Implementation: independently collect nonzero values from each input column in row
order, write zeros above, and place the collected sequence in the last `k` rows of
the same column.  Empty columns remain empty.  This single hypothesis explains all
three visible pairs exactly, so I made one solve revision and stopped after checking.

This is a human work log.  I had earlier rule exposure during the generator review,
but during this solve phase I used only the displayed examples and did not consult
the generator, Racket rule, reference solution, or private query labels.
