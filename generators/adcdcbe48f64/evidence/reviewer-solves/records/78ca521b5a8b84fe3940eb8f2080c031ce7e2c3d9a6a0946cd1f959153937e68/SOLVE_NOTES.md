# Solve work log

## Exposure declaration

This is the required post-repair solve for task `adcdcbe48f64`. I had already
read the task's generator and canonical rule while repairing it, so this episode
is exposed (`earlier-exposure: yes`). During this solve phase I did not reopen the
generator, Racket rule, reference solutions, or private query labels; I used only
the visible examples printed by `python3 review.py solve prepare`.

## Revision 1 — five alternating horizontal tiles

Each output keeps the input height and multiplies the width by five. Reading each
output row in blocks of the input width gives:

1. the original row,
2. the same row reversed left-to-right,
3. the original row,
4. the reversed row,
5. the original row.

This accounts for every visible cell in all three demonstrations, including rows
that happen to be symmetric and therefore do not visually distinguish the two
block types. The implementation performs this row-wise concatenation directly.
No failed natural hypothesis preceded it because the alternating block boundary
is explicit in the asymmetric rows.
