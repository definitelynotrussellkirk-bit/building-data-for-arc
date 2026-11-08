# Solve work log

## Prior exposure

I had already inspected and repaired this generator before this post-repair solve,
so earlier rule exposure is **yes**. During the solve itself I did not open the
Racket rule, generator implementation, reference solutions, private labels, or
older solve explanations. I used only the newly prepared public challenge and my
own Python test.

## Revision 1

The visible examples preserve every component's cells and recolor each connected
green object uniformly. Comparing the labelled shapes suggests a topology rule:

- a component containing a cell with three orthogonal green neighbors becomes 2;
- otherwise a non-branching component with exactly two perpendicular turns
  becomes 6;
- all other components become 1.

This explains the red T shapes, magenta U/S paths, blue straight/L paths, and the
blue degree-4 plus in the examples. The priority of the degree-3 branch matters
for objects that also contain turns.

I first added `test_solution.py`, which runs `solve` on all three public training
examples. It failed on the untouched `NotImplementedError`, proving the test was
live. I then implemented 4-connected component extraction and computed each
cell's internal degree and whether a degree-2 cell is a perpendicular turn.
Remaining uncertainty is only whether some unseen component outside the visible
shape grammar should receive a different fallback; the examples support color 1
for every non-degree-3, non-exactly-two-turn case.
