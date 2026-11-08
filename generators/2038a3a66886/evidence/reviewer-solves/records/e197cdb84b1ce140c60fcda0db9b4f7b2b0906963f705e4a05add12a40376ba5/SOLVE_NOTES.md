# Post-repair visible-only solve work log

This is a human work log. I had already inspected the task's generator and selected
rule while doing the assigned repair, so this episode is **not blind**. During
this solve phase I read only `solve/challenge.json` and my own files; I did not
re-open the generator, Racket authority, canonical ledger, private labels, or an
earlier solution explanation.

## Visible observations

- Every change is horizontal; zero-only rows are unchanged.
- In training example 1, each color appears twice in its row and the zeros between
  those same-color endpoints become that color.
- Training example 2 is decisive against an "exactly two endpoints" rule: colors
  2 and 1 each occur three times, yet the complete leftmost-to-rightmost span is
  filled.
- Training example 3 is decisive against one-span-per-row: rows can contain two
  colors, and each color's own span is filled independently. The two spans remain
  separate rather than filling from the row's first nonzero to its last nonzero.

## Hypothesis

For each row, inspect each nonzero color independently. If that color occurs at
least twice, paint every cell from its leftmost occurrence through its rightmost
occurrence with that color. A singleton color is left alone; rows and colors are
otherwise preserved.

## Rejected alternatives

1. **Fill one outermost span per nonempty row.** Rejected by visible training
   example 3, which has separate 3 and 8 spans in the same row.
2. **Fill only colors occurring exactly twice.** Rejected by visible training
   example 2, where three occurrences still fill the whole outer span.
3. **Fill between every adjacent pair only.** Equivalent on the visible cases,
   but the simpler invariant is the inclusive leftmost-to-rightmost span for each
   repeated color.

## Implementation and probe

`solution.py` copies the grid, preserves first-seen color order, and fills a
color only when it has at least two input occurrences. `test_solution_visible.py`
replays all three visible training pairs before submitting the revision.
