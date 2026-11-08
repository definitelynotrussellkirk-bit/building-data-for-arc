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

## Revision 1 visible feedback and stopping decision

Command (packet root): `python3 review.py blind check --intent solve --note
'Attempted contextual rank: count earlier strictly shorter bars; coherent on
demonstrations 0,1,3 but known unresolved size-6 counterexample in demonstration 2.'`
Exit code: 0. Execution completed; visible_passed 3 / visible_total 4;
reported_label bad; training_admitted false. A command success is not a semantic
pass. The output confirms the known counterexample remains unresolved.

A separate inference-only second view read the same public README and noted the
additional blank row before the first bar in example 2 and its left alignment.
Those observations do not yet justify a transformation switch: ordinary reverse
counting would still predict 9, not 5, for size 6. I have not added a grid-specific
exception or claimed that the partial rule is correct. No real code revision
followed this check, so the sole genuine failed attempt remains intact.

Stopping because the visible data admit a useful partial contextual hypothesis
but I have not found a coherent general rule explaining all four demonstrations.
This solve record is incomplete semantically. It is a retained visible-only
failed attempt; private query correctness is unknown and has not been requested
or inspected. The rest of the assignment should continue with this limitation
reported honestly.
