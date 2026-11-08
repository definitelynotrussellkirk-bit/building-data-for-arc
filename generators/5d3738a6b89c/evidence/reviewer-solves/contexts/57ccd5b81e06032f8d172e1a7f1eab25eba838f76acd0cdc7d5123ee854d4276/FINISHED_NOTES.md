# Post-repair visible-only solve notes

## Revision 1

The full row of 9s separates a prototype dictionary from placement keys. Above
it, full-height 9 columns split the top three rows into 3x3 boxes. The center
color of each box identifies that prototype. Comparing the visible inputs and
outputs shows that every occurrence of a center color below the separator is
expanded using the nonzero cells of its matching box, with the box center
aligned to the occurrence. Cells that would land above the separator or outside
the grid are clipped. The scan must use the original input so newly painted
cells do not become additional anchors.

Implementation plan: parse the separator and boxes, record each prototype as
relative offsets, copy the input, then stamp every matching original lower key.
