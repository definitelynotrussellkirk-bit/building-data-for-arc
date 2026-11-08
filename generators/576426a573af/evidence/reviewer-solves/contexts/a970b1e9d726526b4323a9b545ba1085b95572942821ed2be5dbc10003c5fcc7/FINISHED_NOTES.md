# Final-source visible-only solve record

This is an authored work summary, not a captured token-level model trace.
Earlier exposure: yes. I previously reviewed this task's rule and generator
while repairing it, and completed an earlier solve on the intermediate source.
That earlier solve is retained separately under checks/prior-solve-c36817.
During this newly prepared solve I read only the public challenge, these notes,
and my own Python solution; I did not reopen the rule, generator, reference
solutions, prior solve notes, or private query labels.

Revision 1: use vertical reflection to fill zero cells while preserving each
occupied input cell. The four visible pairs preserve their input dimensions.
The first pair copies the lower pattern upward; the third copies isolated
colors in both directions. The other pairs show that occupied cells keep their
own color even when their vertical partners contain a different color.

The solution computes each output directly from the original input, so copied
cells cannot create a cascading update. I submitted this single revision to the
supported visible-only check. The check result will be recorded below. There
was no failed revision and no deliberate negative probe in this final solve.
The two query inputs are both 10 rows by 4 columns; their correct outputs are
unknown until maintainer scoring.

Observed result: `python3 review.py solve check --intent solve` completed and
reported 4/4 visible pairs passed, query execution completed, and correctness
label `unknown`. I stopped because the single submitted revision fits all
visible examples and executes on both queries. This is an exposed solve of the
final generator bytes, not an independent blind score or training admission.
