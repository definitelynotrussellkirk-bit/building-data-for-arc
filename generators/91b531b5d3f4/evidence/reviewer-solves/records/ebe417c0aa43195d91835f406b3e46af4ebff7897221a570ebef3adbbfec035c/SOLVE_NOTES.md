# Blind solve notes — 91b531b5d3f4

## Visible pattern

Each training grid keeps its shape and all non-1 cells. The first row contains one or more colored column labels. For every `1` below the first row, when the same column has a nonzero/non-1 label in the first row, the output replaces that `1` with the column label. A `1` in an unlabeled column remains `1`.

Evidence:
- Train 1 labels columns 1 and 4 with 9 and 7; every lower `1` in those columns becomes the matching label.
- Train 2 additionally shows unmatched `1`s at columns 8 and 5 remaining unchanged.
- Train 3 shows pre-existing non-1 colors are preserved even inside a labeled column.
- Train 4 shows an unmatched `1` at column 4 remains unchanged while columns 6 and 7 inherit 3 and 4.

## Hypothesis / implementation

Copy the grid. Treat row 0 as a per-column lookup table. Visit rows 1 onward; replace exactly those cells equal to 1 whose header is neither 0 nor 1. Preserve every other cell.

No generator, rule, reference solution, private label, or earlier explanation was consulted.
