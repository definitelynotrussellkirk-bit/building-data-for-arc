## 5ccdbe078da6

**Disposition: current open teaching finding independently reproduced; repair
still needed in ordinary lesson assembly.** Selected source SHA-256
`1e9b22b4d321df7f35c39ee40cded3698f24390b7d331b81daaf4ff1ea70fe5f` and
Racket rule hash `d8da2d7cc24b` match the unresolved source-bound finding in
`evidence/review_index.json`. The selected generator, rule, reference data, and
runtime were left unchanged.

**Exact reproduction.** Generate seed `0`, difficulty `easy`, sample indices
`0,1,2` as the three demonstrations and index `3` as query. All four inputs pass
`self_check`; their review-mirror outputs match fresh canonical Racket execution.
Both declared competitors `numeric_ascending` and `ignore_lines` fit all three
Racket-labeled demonstrations and disagree with the query label:

- `numeric_ascending` predicts 4 where Racket produces 2 at zero-based cells
  `(1,2)`, `(2,2)`, and `(3,2)`.
- `ignore_lines` leaves `(2,1)` as 0 while Racket produces 9.

The other three choices of held-out position in this same four-pair window
produce no ambiguity against the six declared rivals. This demonstrates why
checking a different query rotation or only aggregate witness availability
does not establish that the ordinary three-demo/query-3 lesson teaches the rule.
The scope is a single exact current production-shaped window, not a new estimate
of ambiguity rates across the full generator distribution.

**Per-input semantics remain sound in this bounded check.** The four retained
canonical input/output pairs also pass the validator, agree with Racket, and
agree with the Python mirror. All eight checked labels are therefore consistent;
the defect is lesson identifiability against executable wrong rules. The
task's notes and handoff already acknowledge this distinction and describe an
optional exact-cover selector. That optional tool and its old passing tests do
not change which demonstrations an ordinary sequential lesson contains; this
audit did not rerun or claim integration of that selector.

**Suggested next action.** Preserve the current rule and generated input
support. Route ordinary lesson construction through a demonstrated finite-rival
cover or add an equivalent assembly gate that rejects this concrete ambiguity.
Keep query outputs out of demonstration selection. Validate the actual permitted
query rotations after selection. This audit tested the task's six declared
rivals; shared generic object/position rivals and arbitrary programs remain
outside its claim.

**Evidence.** `checks/audit/5ccdbe078da6/probe.py` uses the supported selected
loader and relocated canonical Racket runtime. Exact source/rule hashes,
all four generated input/output pairs, all rival predictions, disagreement
cells, canonical verification, and current-open-audit bindings are retained in
`checks/audit/5ccdbe078da6/report.json`. The exact command and exit status are
in `checks/audit/5ccdbe078da6/commands.json`. The probe exited 0 after executing
eight Racket inputs; exit 0 records successful reproduction, not resolution.
No full battery, historical return sweep, blind solve, or private solve was used.
