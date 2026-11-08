# Solve work log

## Exposure declaration before solving

I had not opened task `510b12f6a12a`'s generator, Racket rule, notes, reference
solutions, private labels, or prior solve explanations.  I had only read the
packet-level assignment instructions and `solve-blind/challenge.json`.

## Revision 1 — crossing rays with blockers

Visible structure: every input places color 2 only in the top row, color 1 only
in the left column, optional color-5 cells in the body, and otherwise zeros.
The outputs discard the headers and place color 6 at selected body cells.

Initial candidate: output the Cartesian product of rows marked by a left-edge 1
and columns marked by a top-edge 2.  This exactly explains training example 3,
which has no color-5 cells, but it over-predicts training examples 1 and 2.

Refinement from the counterexamples:

- In training example 1, the left ray on row 7 reaches the first selected column
  but a 5 at column 3 prevents the crossing at selected column 4.
- In training example 2, a 5 immediately after the row marker prevents every
  crossing on that row; a 5 in one selected column blocks that top ray below it.
- Therefore a 1 emits rightward and a 2 emits downward; color 5 blocks either
  ray.  A body cell is 6 exactly when both unblocked rays reach it.

Implementation probe: for each selected body coordinate `(r, c)`, check that
there is no 5 in row `r` from column 1 through `c`, and no 5 in column `c` from
row 1 through `r`.  Return a zero grid with 6 at coordinates satisfying both.

Remaining uncertainty before checking: whether a blocker cell itself should be
considered merely opaque or also retained in the output.  All visible outputs
remove blockers, so the program emits only 0 and 6.
