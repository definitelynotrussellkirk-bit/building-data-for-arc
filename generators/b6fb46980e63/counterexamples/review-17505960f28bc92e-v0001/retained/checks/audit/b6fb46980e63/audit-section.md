## b6fb46980e63

**Findings-only audit; reproduced generation/validation defects. No target or
shared source was edited.** Inspected version 1.2.1, generator SHA-256
`5613165773fea5f66c0a530bb9b9f74299ed5a0dd093ec2e82477a2307077be6`.
Official `arcpuzzles apply` executed canonical rule fingerprint `e5a0bd5fed6a`,
rule-text SHA-256
`faffb6e3b338c9bbcc29376b37350bfc78783e6839f3c16929b4dad124c37436`.
The raw canonical ledger program SHA-256 is separately
`b1bfaf0222f4eafdaace8d7ef12f1cdd6e0251e3d002d922918d5efc8723b6da`;
the apply receipt hashes the executable wrapped reference text.

**A1 — reproduced defect: ordinary generation silently loses required hole
classes.** The declared invariant requires at least one 0-hole, 1-hole and
2-hole component. In a finite census of seeds 0–19 inclusive, sample index 0,
across easy/medium/hard, **27/60 deterministic draw tuples** lacked at least one
mandatory class: **14/20 easy, 7/20 medium, 6/20 hard**. There were **59 unique
inputs**, and `self_check` accepted **60/60**. The source tries 60 placements per
shape and then continues without detecting failure. Its validator checks lower
cell colors but does not enforce component count or hole-class coverage.

The first ordinary witness, `generate(0, 0, difficulty="easy")`, contains exactly
two lower components, with hole counts 0 and 1; class 2 is missing. It passes
`self_check` and was produced without overrides. Official Racket application
succeeds on that witness, so this is a generator/domain contract defect, **not a
claimed wrong output**. Its input hash is
`6530287c0717623020272201175d8059f62a9b207ee44f251052098b8dc4d021`.
Evidence: `checks/audit/b6fb46980e63/probe.json`, `input.json`, and `racket.json`.

**A2 — reproduced defect: an advertised degenerate is accepted although the
reference cannot execute it.** `generate(0, 0, texture="no_legend")` returns the
advertised no-legend texture and `self_check` returns `[]`. Official application
exits **1**, with no output and Racket error `take: contract violation` because
the legend has zero entries and the rule requires three. This is an explicit
degenerate override rather than an ordinary random sample. It is outside the
main three-entry-legend invariant, and the validator fails to reject it.
Evidence: `checks/audit/b6fb46980e63/no-legend-input.json`,
`no-legend-racket.json`, and `no-legend-apply.log`. The failed application is
retained, not counted as a pass.

**Existing domain drift reconfirmed.** Read the existing unresolved
`review-921182f345e32906:v0001` audit and its retained summary. The current
validator still rejects **5/5 canonical inputs** because lower cells are not
restricted to color 5. Actual Racket execution matches the stored canonical
labels on **5/5**. This independently confirms generator/validator drift rather
than a canonical-rule labeling defect. Evidence:
`checks/audit/b6fb46980e63/canonical-racket.json`, `canonical-expected.json`, and
the canonical validation records in `probe.json`. No task-local tests directory
or focused target tests are present in this packet.

**Limits and next action.** Findings are bound to the source hash above and this
finite sample. Only the first ordinary omission, the explicit no-legend case,
and the five canonical inputs received fresh official Racket execution; the
other ordinary draws were inspected with an independent four-neighbor
component/hole census. No new output-shortcut claim, all-seed proof, safety
approval or target repair is asserted. A task-local repair should make required
placement failure explicit (retry or fail the draw), enforce legend and hole
coverage in validation, and decide how to admit the canonical body palette.
Exact commands, exit codes and evidence paths are in
`checks/audit/b6fb46980e63/commands.json`; combined counterexample provenance is
in `checks/audit/b6fb46980e63/counterexample.json`.
