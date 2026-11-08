Task `2a5919c40197`, generator version `2.0.1`; final SHA-256 `ab882fbcfe024233a84e2347b2463f99262a4efb7a2d5c6f16d7ca091994ab6f`.
Defect: 33 strict-scalar probes showed `seed`/`sample_index` accepted booleans, floats, strings, or negative indices.
Repair: both public entry points now require literal nonnegative integers, without changing any lawful generated grid.
Battery: before 11/12 green (`defect_lint` failed); final 12/12 green with 0 advisory, failed, interrupted, or pending stages.
Portable focused tests: final 15/15 passed, including 15/15 in a clean full-packet replay; the retained first run was 12/15 and exposed a task-snapshot import collision that was then fixed.
Lessons use 3 demonstrations plus 1 query, alternating 3×3 anchors and width-extension witnesses by accepted sample index.
Lesson census: 300/300 production lessons and 1,200/1,200 held-out query rotations were identifiable; 0 ambiguity, hook, or scoring errors.
Parametric assessment: proposed `line_axis∈{row,column}` prototype only; 48 Racket labels matched and 24/24 rotations distinguished the setting.
No Racket authority changed in this review; canonical row program SHA-256 remains `72e69fa2d29a33575fd623dc610554eb99b989013d47e570ee0b59aee253b339`.
Audit-only findings reproduce unresolved shortcuts in `1a21a4a82b48` and `67e9e17efb62`; neither audited source was modified and neither blocks this repair.
Remaining blocker: none for the selected repair. Production integration of the parametric prototype remains a separate maintainer decision.
Acceptance: routine.

# Findings

| ID | Affected task/path | Finding and evidence | Patch status | Final result |
|---|---|---|---|---|
| R1-SCALAR | `generators/2a5919c40197/generator.py` | Invalid replay coordinates were accepted; see `checks/before/checks/2a5919c40197_before_defect_lint.log` and `generators/2a5919c40197/counterexamples/strict-scalar-contract.json`. | Repaired and regression-tested. | `defect_lint` green; full battery 12/12 green. |
| R2-PARAM | `generators/2a5919c40197/workspace/parametric/` | A bounded structural parameter can switch the classified axis while preserving the canonical row program as the default. | Proposed prototype only; not wired into production. | 48/48 Racket labels matched; 24/24 episode rotations identifiable. |
| R3-PORTABLE | Parametric self-check loader | The first portable snapshot imported the same snapshot through two layouts and failed 3 tests. | Fixed locally by accepting only package roots inside the same supplied snapshot and compiling the exact selected generator bytes. | Final portable task stage 15/15 green. |
| A1-SIZE | Audit `1a21a4a82b48` | Three easy demonstrations permit “same-size, then lowest-color” selection, while sample 3 refutes it. | Audit only; source unchanged. | Reproducer valid; canonical Racket output differs from rival. |
| A2-POSITION | Audit `67e9e17efb62` | All 12 canonical pairs and the sampled demonstrations are left-anchored, permitting a left/right-conditional serialization rival. | Audit only; source unchanged. | Right-anchored sample 3 is valid and Racket-confirmed to refute the rival. |

# Selected repair

## R1-SCALAR — root cause and change

The baseline generator had two inconsistent paths: `generate` passed values into `GenCtx` without a literal-type check, while `schedule_profile` used coercive `int(...)` handling. The immutable before battery therefore accepted 33 invalid calls across easy/default/hard probes: booleans and numeric-looking floats/strings for both coordinates, plus negative sample indices. The before summary is `checks/before/checks/2a5919c40197_before_battery_summary.json` and the decisive log is `checks/before/checks/2a5919c40197_before_defect_lint.log`.

A focused test was added first and observed failing in `checks/tdd-red-strict-scalars.log`. The implementation adds one `_validate_nonnegative_int` helper and calls it from both `generate` and `schedule_profile`; `checks/tdd-green-strict-scalars.log` records the focused green run. The change is deliberately narrow: lawful integer requests retain their former deterministic outputs and profile schedule, while invalid replay coordinates fail before random-context construction.

The complete final battery is source-bound in `checks/after/checks/2a5919c40197_after_battery_summary.json`: 12 green stages, generator SHA-256 `ab882fbcfe024233a84e2347b2463f99262a4efb7a2d5c6f16d7ca091994ab6f`. The final portable task-test receipt is `checks/task-tests-v2/result.json` with 15/15 passing. The earlier 12/15 result under `checks/task-tests/` is retained because it exposed R3-PORTABLE rather than being erased.

## Curriculum and shortcut check

The intended law remains full-row uniformity: every uniform row becomes `5`, every mixed row becomes `0`. The default schedule alternates exact 3×3 anchors with width-extension inputs that contain a mixed row whose first three cells agree. Thus the strongest canonical shortcut—classifying only the first three cells—fits all five canonical pairs but is refuted inside every complete generated lesson and every held-out query rotation checked.

The large final census, `checks/lesson-census-v1.summary.json`, used 100 lessons per difficulty band. It materialized 300/300 lessons, 1,200 labeled pairs, and 1,200 query rotations, with 1,139 unique exact inputs and zero materialization, ambiguity, hook, or scoring errors. This is finite evidence against the declared rival, not a proof against every possible hypothesis.

The post-repair visible-only solve is bound to the same final generator SHA in `solve/summary.json`. It passed all 3 visible examples on revision 1 and honestly records earlier rule exposure as `yes` and reference consultation during solve as `false`. The earlier blind assignment `9199b47fab1e` remains separate in `solve-blind/summary.json`; its 3/3 visible pass retains the unresolved nonconvex-room metric ambiguity.

# Parametric-rule assessment

## R2-PARAM — proposed, not integrated

The runnable extension under `generators/2a5919c40197/workspace/parametric/` introduces exactly one source-bound parameter, `line_axis`, with allowed values `row` and `column`; `row` is the canonical default. The parameter is selected once per episode from seed parity. Controlled 4–7-cell grids contain exactly one uniform row and exactly one uniform column, so the same input has different labels under the two settings and each three-demonstration/one-query episode identifies its hidden setting.

`checks/parametric/line-axis-v2/report.json` records:

- row-program SHA-256 `72e69fa2d29a33575fd623dc610554eb99b989013d47e570ee0b59aee253b339` and column-program SHA-256 `a7d1754c61ab24c957309aba99c0ec6b081a038a872374cdc0bb8af29923f57a`;
- byte-exact reproduction of all 5 canonical pairs under the row setting;
- 48 real Racket labels, all matching the independent Python assertions;
- 6 episodes covering both settings and 24/24 identifiable query rotations;
- a same-input witness whose row and column outputs differ.

The public challenge projection omits the hidden parameter, program text, and query answers. Limits are explicit: this finite probe covers only two axes and a deliberately controlled input family; it does not establish universal identifiability or authorize changing the production generator.

## R3-PORTABLE — integration defect found and repaired

The initial task snapshot passed 12 tests and failed 3 because `puzzle_generators` had already been imported from the snapshot’s repository mirror while the prototype requested its equivalent execution-layout package. The full traceback is retained in `checks/task-tests-command.log` and `checks/task-tests/result.json`.

The fix is task-local: the prototype accepts either package layout only when it resolves inside the same caller-supplied snapshot root, rejects cached dependencies outside that root, and compiles the exact selected generator bytes. `checks/task-tests-v2-command.log` and `checks/task-tests-v2/result.json` show 15/15 passing in a fresh portable snapshot. The shared strict loader was not weakened.

# Audit-only findings

The exact source-bound findings and supported Racket commands are in `AUDIT.md`. Both are lesson-design ambiguities, not claims that their canonical rules execute incorrectly. No audited generator was edited.


# Final clean replay

The candidate delta ZIP was replayed against the exact original source ZIP in a new full extraction, not a runtime closure. `checks/final-replay-v1/replay.json` records all 94,130 original files extracted, Git rooted at the replayed `WORK/`, `git apply --check` and `git apply` both exiting 0, all eight changed paths matching their reviewed hashes, and final generator SHA-256 `ab882fbcfe024233a84e2347b2463f99262a4efb7a2d5c6f16d7ca091994ab6f`.

From that clean checkout, the selected focused suite passed 15/15 (`checks/final-replay-v1/focused-tests.log`). The parametric verifier independently repeated 5/5 canonical row matches, 48 Racket labels, and 24/24 identifiable rotations (`checks/final-replay-v1/parametric/report.json`). These receipts bind the final source patch; the deliverable is rebuilt afterward only to include the receipts and reports.

# Self-review

The selected production delta adds only argument validation, so it cannot narrow or bias the distribution of valid generated examples; deterministic outputs for valid integer coordinates are unchanged. The existing width-extension witness remains mandatory, and the 300-lesson/1,200-rotation census found no surviving instance of the declared first-three-cells shortcut, while the finite-search limitation is kept explicit.
