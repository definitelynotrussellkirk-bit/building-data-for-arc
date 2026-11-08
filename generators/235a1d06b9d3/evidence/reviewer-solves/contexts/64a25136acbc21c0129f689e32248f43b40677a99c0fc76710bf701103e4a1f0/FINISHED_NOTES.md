# Solve work log

## Prior exposure

Before this solve I had read only the packet-level instructions. I had not opened
this task's generator, canonical rule, notes, reference solution, private labels,
or audit evidence.

## Revision 1 — header plus horizontal projection

Across all three visible examples, the most frequent color is the background.
The first row carries a horizontal pattern in a second color, while column 0 of
alternating lower rows carries a vertical pattern. Every output has exactly three
rows:

1. input row 0 unchanged;
2. input row 1 unchanged;
3. a background row whose cells are color 6 exactly where input row 0 is not the
   background.

This explains the examples even when color 6 is already one of the input marker
colors (train example 2). I tested the unimplemented scaffold first and observed
the expected `NotImplementedError`, then implemented this rule. Remaining
uncertainty: the visible examples do not independently vary the vertical stripe
schedule, so it may be structural context rather than information used by the
output rule.
