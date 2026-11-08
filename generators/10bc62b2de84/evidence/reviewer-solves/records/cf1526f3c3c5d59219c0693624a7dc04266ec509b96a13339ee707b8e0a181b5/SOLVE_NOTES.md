# Visible-only solve notes

## Revision 1

From the three visible training pairs:

- Each nonzero 4-connected component is preserved exactly inside its own bounding-box crop.
- Components appear in output order by their input bounding-box left column.
- Crops are separated by one zero column.
- Output height is the maximum crop height.
- Shorter crops are shifted downward so their bottom row matches the tallest crop's bottom row. This is directly visible in examples 0-2 because object heights differ.

Implementation plan: extract all nonzero 4-connected components, sort by minimum column, crop each bbox from the original grid, allocate the packed canvas, and paste nonzero crop cells bottom-aligned.
