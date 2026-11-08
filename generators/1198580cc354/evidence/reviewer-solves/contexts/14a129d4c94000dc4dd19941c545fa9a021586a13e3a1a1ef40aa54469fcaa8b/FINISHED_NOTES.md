# Post-repair visible-only solve notes

## Observation

Each training input has colored cells only in the top row, plus one or more
color-9 cells lower in the grid.  The output copies each top-row color straight
down its own column.  A 9 remains unchanged and stops only the beam in that
column; it does not stop neighboring columns.  Cells below the blocker remain
0.  An unblocked seed reaches the bottom row.

Color 1 behaves exactly like the other seed colors in all three examples, so
it is not background or a special marker.  The output shape always equals the
input shape.

## Hypothesis implemented

For every top-row cell whose value is neither 0 nor 9, scan downward in the
same column.  Replace 0 cells with the seed color until the first 9; preserve
that 9 and stop.  Leave all other cells unchanged.

## Query-specific checks

- Query 0 has four seeds.  Columns 2, 6, and 8 stop at blocker rows 4, 6, and 7;
  column 3 reaches the bottom.
- Query 1 has four seeds.  Columns 3 and 4 stop at row 5, column 5 stops at row
  4, and column 6 reaches the bottom.

No reference source, generator source, prior solution, or private query label
was consulted during this solve phase.  I had earlier rule exposure from the
required generator review, so this is explicitly not a blind solve.
