# Solve work log

## Prior exposure

I had already inspected this task's generator and canonical rule while performing
the assigned repair, so this is an exposed post-repair solve, not a blind solve.
For this solve phase I did **not** reopen or consult the generator, Racket source,
reference solutions, private query labels, or prior solution explanations.  The
hypothesis below was checked only against the visible examples produced by
`solve prepare`.

## Revision 1 hypothesis

The output keeps the same shape and changes only certain columns.

1. Read the nonzero cells of each column from top to bottom.
2. A column is selected exactly when its **last nonzero cell has color 5**.
   Train 2 is the key selector counterexample: column 1 contains an internal 5
   but ends in color 3 and is left unchanged, while columns 7 and 10 end in 5
   and are expanded.  Other multi-marker columns that do not end in 5 also stay
   unchanged.
3. In a selected column, process the original markers top to bottom.  The first
   marker's color fills from row 0 through that marker.  Each later marker's
   color fills the rows after the preceding marker through the current marker.
   Thus the current/lower marker owns the blank interval immediately above it.
4. Rows below the final marker are untouched.  Train 2 shows the final 5 at row
   11 while row 12 remains unchanged.
5. Use only the original marker positions; inserted fill cells do not become new
   markers or affect other columns.

This explains every changed and unchanged cell in all three demonstrations.  A
plausible alternative—letting the upper marker own each gap—is contradicted by
Train 1, where rows 4–5 in column 6 take color 9 rather than 6.  Selecting any
column that merely contains a 5 is contradicted by Train 2 column 1.

## Implementation

`solution.py` copies the grid, gathers original nonzero markers per column,
filters on final marker color 5, then fills the inclusive intervals described
above.  It makes no assumptions about fixed dimensions, marker count, palette,
or the final marker being on the bottom row.

## Remaining uncertainty

The visible examples strongly distinguish the selector, ownership direction,
first-segment boundary, and floating-tail behavior.  They cannot rule out every
contrived rule that agrees on these examples, but no unresolved natural rival
remains for the two visible queries.
