# Post-repair visible-only solve log

Earlier exposure: yes. Before this required solve phase I had already inspected this
task's generator and canonical authority while repairing it. During the solve phase,
I consulted only the visible challenge printed by `review.py solve prepare`; I did
not reopen the generator, authority, canonical data, reference solutions, or private
labels.

## Revision 1

Hypothesis: process columns independently. In each column, scan from top to bottom.
If the column is empty, leave it zero. Otherwise take the first nonzero cell's color
and fill the entire column with that color; any lower nonzero cells are distractors.

Visible evidence:

- Example 0 has column 4 containing a 5 above a 9, and the whole output column is 5.
  This directly rules out using the bottommost seed or requiring a single seed.
- Example 1 has two stacked columns. Column 0 starts with 9 then has lower 1s and
  becomes all 9; column 1 starts with 1 then has lower 9s and becomes all 1.
- Example 2 repeats the conflict: column 1 has 7 above 1 and becomes all 7, while
  the single-seed column 2 becomes all 1.
- All other columns remain zero and the grid shape is unchanged.

The two visible queries have the same structure, including top/bottom conflicts, so
this rule determines both outputs without an unsupported tie-breaker.
