# Solve work log

Earlier exposure: none. I did not inspect the generator, Racket rule, reference
solutions, private labels, prior notes, or the assigned repair target before this
solve. I used only `challenge.json` and local tests against its visible pairs.

## Revision 1 — marker-controlled cyclic row shift

Each input has one extra left column. Deleting it explains the first two training
pairs directly. In the third pair, the sole color `2` in that control column is
at row 1, and the remaining grid is cyclically shifted down by one row: the last
row becomes first. This suggests the row index of `2` is the downward rotation
amount. The two tests place `2` at rows 1 and 3, respectively, which exercise
nonzero shifts.

I first added `test_solution.py`, which checks all visible training pairs; it
failed on the untouched `NotImplementedError`. The implementation now locates
`2` in the first column, removes that column, and rotates the remaining rows down
by the marker's zero-based row index. Alternatives considered were merely deleting
the first column or moving the marked row to the top; both contradict training
pair 3. Remaining uncertainty: the visible examples do not show multiple or
missing `2` markers, so the solution assumes exactly one, as every shown input has.
