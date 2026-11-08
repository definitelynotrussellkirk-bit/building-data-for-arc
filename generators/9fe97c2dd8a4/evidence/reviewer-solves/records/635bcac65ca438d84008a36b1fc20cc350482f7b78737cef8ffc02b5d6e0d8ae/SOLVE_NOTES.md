# Visible-only blind solve work log

This is a human-readable model work log, not a token-level model trace.
Read only packet protocol documents and this episode's public README/challenge.
No generator, rule, canonical helper, task notes, audit record, reference solution,
or private answer file has been opened. Earlier rule exposure: no.

## Observations

All four visible demonstrations preserve the input and add one pixel in each bar
row at the column selected by the lone gray marker in the first row. Horizontal
bars may themselves be gray, so excluding color 5 globally would be incorrect.
Colors of the bars and horizontal starts seem irrelevant to the added label.
The visible size/label sequences are:
- example 0: sizes [2, 3, 4], labels [1, 4, 9];
- example 1: sizes [2, 2, 5, 2], labels [1, 1, 9, 1];
- example 2: sizes [6, 6, 2, 3], labels [5, 5, 1, 4];
- example 3: sizes [4, 4, 2, 3, 3], labels [1, 1, 1, 4, 4].

A fixed map by length and a global dense rank do not fit. In particular size 4
has label 9 in example 0 but label 1 in example 3, despite identical sets of
distinct lengths. Color occurrence, purely geometric gap, ordinary competition
rank and equal-size frequency also did not provide a coherent explanation.
These were reasoning probes, not checker submissions.

## Revision 1 hypothesis

Use palette [1, 4, 9, 5], with index equal to the number of previously encountered
bars strictly shorter than the current bar. This predicts all rows in examples
0, 1 and 3, including the context change for size 4, but predicts label 1 for both
size-6 bars in example 2 where the visible output uses 5. I am checking this as
an ordinary attempted solution despite the known counterexample; it is an honest
partial rule and is not an intentional teaching negative. This check will record
visible failure, not certify hidden query correctness.
