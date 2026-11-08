# Visible-only blind solve: c5dd8036311b

Earlier exposure: no known exposure to this task's generator, rule, notes, or solutions.
Only the packet instructions and solve-blind/challenge.json were consulted. This is
an assistant-authored experiment summary, not a token-level conversation trace.

## Revision 1 — marker-dependent vertical extensions
The visible examples have one horizontal nonzero row. The input is preserved;
markers of color 2 gain an upward stem of three 1s and a 2 cap four rows above,
while markers of color 8 gain two 1s and an 8 cap three rows above. Positions,
row height and the number of markers vary. I implemented those two observed
extensions, independently per marker, preserving all other cells.

Probe: the supplied unimplemented stub did not reproduce the visible examples
(checks/blind-stub-test.json); that is a scaffolding check, NOT a failed natural
solve attempt. No deliberate wrong solution was submitted. The visible pairs
are the regression tests. The query inputs contain only 8 markers, whose behavior
is directly demonstrated in the first visible pair. Out-of-frame clipping is a
reasonable implementation boundary, not a behavior established by these examples.

Remaining uncertainty: a different unseen rule could fit these three examples;
query correctness is masked and must be scored independently.
