# Fresh visible-only solve after repair: d2b3402dde86

## Exposure

Earlier rule exposure: **yes**. I repaired this task's generator and inspected
its rule before this solve. This is an exposed post-repair solve, not a blind
attempt. During the solve I consulted only the visible preparation display and
my own new Python solution. The generator, Racket source, canonical-data
helpers, prior solution explanations and private query labels stayed closed.

These are authored work notes, not a captured token-level model trace.

## Observations and hypothesis

- Example 0: Input: 11 rows × 13 columns. Output: 3 rows × 4 columns.
  Non-zero input cells span rows 2 through 8 and columns 2 through 10, a
  7 × 9 rectangle. The output copies its first three rows and four columns.
- Example 1: Input: 10 rows × 10 columns. Output: 3 rows × 3 columns.
  Content spans rows 2 through 7 and columns 2 through 7, a 6 × 6 rectangle.
  The copied top-left 3 × 3 contains an entirely zero first row, retained in
  the visible output. Cropping the answer again would lose that row.
- Example 2: Input: 13 rows × 10 columns. Output: 4 rows × 2 columns.
  Content spans rows 2 through 10 and columns 1 through 5, a 9 × 5 rectangle.
  The output takes its upper-left four rows and two columns.

The common transformation is: find the bounding rectangle of all non-zero
cells, take half its height and width rounded down independently, and copy
the upper-left rectangle without removing its zero rows/columns.

The visible odd rectangles distinguish flooring from ceiling and from a fixed
3 × 3 crop. The second example distinguishes preserving blank answer borders
from trimming the result. No color remapping is evident.

## Revision 1

Wrote a standalone `solve(grid)` using only integer coordinates and slices.
It imports neither the generator nor any reference/runtime helper. It preserves
input data and retains all zeros inside the selected rectangle. No failed
revision was manufactured. Query 0 has a 12 × 10 input and Query 1 has a
10 × 13 input; both query outputs and their true dimensions remain unknown.

## Check and stopping reason

Pending the first visible-only checker result. Hidden-query correctness will
remain unknown regardless of visible-example agreement.
