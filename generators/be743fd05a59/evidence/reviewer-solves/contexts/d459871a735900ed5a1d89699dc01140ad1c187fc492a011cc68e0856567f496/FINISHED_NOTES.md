# Solve work log

## Prior exposure

I had not opened this task's generator, Racket rule, canonical entry, private labels,
reference solution, audit records, or any earlier solution explanation. I had only
read the packet-level instructions and the visible examples produced by
`solve_episode.py blind prepare`.

## Hypothesis

Comparing each input with its output, every newly painted cell is color 5 and is
exactly one row down and one column left of a color-9 cell. The destination is
painted only when it is in bounds and background (0); existing nonzero cells are
preserved.

Evidence across the demonstrations:

- Example 0: the five 9s nominate `(2,3)`, `(3,7)`, `(4,1)`, `(6,2)`, and
  `(7,5)`. `(2,3)` is already color 3, so the other four alone become 5.
- Example 1: `(2,5)` and `(4,2)` become 5; the destination down-left of the 9
  at `(5,0)` is out of bounds.
- Example 2: the two upper destinations are respectively out of bounds and
  occupied by color 3, while `(6,4)` and `(6,7)` are painted 5.

The varying color-3 shape appears to serve as an obstacle/collision witness rather
than as a template. A competing idea that the 9s should be connected by lines was
rejected because example 0's four added cells are independent one-step offsets and
do not form connecting paths.

## Implementation and probe

`solve` copies the grid, scans the original cells, and paints each legal empty
`(row+1, column-1)` destination with 5. It uses the destination row's actual
length, so it also avoids assuming rectangular input.

Before implementation, a local visible-example harness failed with the template's
`NotImplementedError`. After implementation I reran the same harness and then the
official visible-only checker.

## Query predictions

For query 0, the expected added 5s are `(1,9)`, `(3,8)`, `(4,0)`, and `(6,3)`.
For query 1, the expected added 5s are `(1,7)` and `(8,4)`; `(7,1)` is already
color 1 and must remain unchanged.

Remaining uncertainty is limited to whether a hidden destination should overwrite a
nonzero cell. All three demonstrations consistently support preserving occupied
cells, including both obstacle colors and boundary cases.
