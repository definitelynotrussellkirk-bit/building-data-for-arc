# Solve work log

## Exposure declaration

I had already reviewed this task's generator and rule authority before this
solve, so this is an exposed solve. During this solve I did not reopen the
generator, Racket authority, reference solutions, private labels, or the prior
solve notes retained under `checks/`.

## Revision 1

Using only the visible examples in `challenge.json`, I compared the retained
color with scan order and frequency:

- Example 0 retains color 7. Its first occurrence is the first nonzero cell in
  row-major order, while it is the *least* frequent nonzero color (2 versus 3
  and 4), so "most frequent" is false.
- Example 1 retains color 5. Again it is the first row-major nonzero, but its
  count 3 is between counts 2 and 4, so no fixed frequency rank works.
- Example 2 retains color 9. The first row is empty and the first nonzero is 9
  at `(1, 3)`; here 9 is the most frequent color. This also shows that the
  selector is not tied to the first row or a fixed coordinate.

Hypothesis: scan row-major for the first nonzero color, preserve every cell of
that color, and replace every other nonzero color with 0. Preserve the input
shape. For an all-zero grid, return an unchanged copy.

Predictions:

- Query 0: the first nonzero is 8 at `(8, 5)`, so retain the two 8 cells and
  erase colors 7 and 9.
- Query 1: the first nonzero is 1 at `(0, 1)`, so retain all three 1 cells and
  erase colors 5 and 9.

Remaining uncertainty before checking: none among simple frequency, fixed
position, or last-color alternatives; all three visible examples distinguish
those from the scan-order rule.
