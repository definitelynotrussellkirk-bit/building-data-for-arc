# Solve notes

This is a human-readable work log based only on the prepared visible examples.

## Hypothesis

The first cell of each row is a header. If it is nonzero, that value is copied
across the entire row. If it is zero, the whole output row is zero.

Evidence:

- Train 0 has only first-column markers, and exactly those rows become solid.
- Train 1 is decisive: nonzero cells in zero-header rows disappear, while
  conflicting nonzero cells in marked rows are overwritten by the first-cell
  color.
- Train 2 confirms the behavior at the top and bottom boundaries.

The transformation preserves every row length and the number of rows. The two
queries therefore use the same row-local operation independently on each row.
