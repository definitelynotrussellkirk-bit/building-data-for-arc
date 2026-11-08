# Solve notes

## Visible-example hypothesis

Treat columns independently.  A column fires only when it contains exactly two
nonzero cells and both cells have the same color.  The output fills every cell
from the upper endpoint through the lower endpoint with that color.  All other
columns are copied unchanged.

## Discriminating examples

- Train 2 has two values in column 7, but they are colors 3 and 6.  That column
  stays unchanged, rejecting the rival “fill between any two markers.”
- Train 3 has colors 5, 2, 5 in column 8.  The matching outer values do not
  trigger because there are three nonzero cells, rejecting “use matching outer
  endpoints despite blockers.”
- Train 4 has a singleton color 1 in column 0 and it stays a singleton,
  rejecting singleton extension.
- Columns with valid pairs can begin or end at an edge; test 1 column 0 and test
  2 column 5 exercise that case.

## Implementation decision

Scan each column, collect its nonzero `(row, color)` entries, and fill only when
there are exactly two entries with equal colors.  Copy first, so mismatches,
blocked columns, singletons, empty columns, and unrelated colors are preserved.
No reference implementation or hidden label was consulted during this solve.
