# Review — generator 3ab9aab86992
Task `3ab9aab86992`, generator version `2.2.0`, final SHA-256 `14f3c3a81127c7f65da3bd837ef287021fb5d8cba1c61f65dc76ac8d5c8af384`.
Baseline defect → repair: negative or lossy scalar call arguments were accepted; seed/sample index/difficulty are now strictly validated.
Teaching defect → repair: a prior four-slot lesson schedule left 2/48 query rotations ambiguous; every final three-demo holdout refutes `complete_all_corners`.
Final checks: strict battery 12/12 green and portable task tests 118/118 passed on the final source.
Lessons: 3 demonstrations + 1 query; ordered period-4 cardinality schedule, seed-rotated, with explicit overrides taking precedence.
Production/rotation census: 300/300 lessons, 1,200/1,200 query rotations, 1,200 unique inputs, zero declared-rival ambiguity or scoring errors.
Fixed-schedule census: all 12 band/start lessons and all 48 query rotations passed at schedule seed 0.
Racket authority: canonical normalized hash `bbdf13ba2dfd` and exact program SHA `c83accbef454499a8c9af94eaf34ddd2d50551e7312ed9a0360c34a00985fd89` are unchanged; execution parity passed.
Parametric status: `corner_basis={elbow, missing}` is a runnable proposed prototype only, not production/catalog/training approval.
Remaining blocker: none for the selected repair; finite-rival and prototype-domain limits are documented below. Acceptance: routine.

## Scope and outcome

This return repairs only `repo/generators/3ab9aab86992/`, adds focused tests and a
separate parametric prototype, answers the assigned shortcut question, preserves two
adversarial audit findings, and includes both required solve records. The canonical
transformation remains: each tiny monochrome L's occupied elbow selects the
corresponding enlarged border-L output corner in the same color.

The prior approved repair `review-248201d73dc2f3a9:v0001` was used as a lead for the
current generator domain. The unresolved lesson-rotation finding from
`review-38c015cb27208030:v0001` was reproduced as the teaching target; current-source
measurements, not the prior claims, determine this return.

## Finding table

| ID | Finding / deliverable | Affected path | Reproducer or evidence | Status |
|---|---|---|---|---|
| R1 | Negative `sample_index` and nonliteral integer calls were accepted | `generator.py` | `tests/test_review_20261021.py`; before defect lint | Fixed; final defect lint green |
| R2 | Multi-axis rejection lacked machine-readable conflicting-axis names | `generator.py` | focused test `test_multi_axis_rejections_name_the_conflicting_controls` | Fixed with `ValueError.incompatible_axes` |
| R3 | Lesson schedule could fail arbitrary query rotations against `complete_all_corners` | `generator.py` | `lesson-census-final*`, `schedule-census-final.json` | Fixed for the declared rival and four-slot schedule |
| R4 | First repaired schedule over-restricted default density | intermediate source | `checks/after/` dist-gate failure | Reversed; final schedule restores median object count ≥3 |
| P1 | Small meaningful original-family rule parameter was missing | `workspace/parametric/` | `checks/parametric-final-source/evidence.json` | Proposed prototype; isolated from production |
| Q1 | Strongest verified canonical shortcut is `complete_all_corners` | `counterexamples/current-shortcut.json` | `checks/main-shortcut-final.json` | Exact emitted counterexample retained |
| A1 | `eca9af4f6c53` ignores advertised `n_blocks`/`palette_size` | untouched audit target | `checks/audit/eca9af4f6c53/declared-axis-probe.json` | Reproduced audit finding; no repair attempted |
| A2 | `891b61bb5d4d` ignores advertised size/helpful-texture controls | untouched audit target | `checks/audit/891b61bb5d4d/declared-axis-probe.json` | Reproduced audit finding; no repair attempted |

## Before and after

The completed baseline battery is retained at
`checks/before/checks/3ab9aab86992_before_battery_summary.json`. It reported 10
green stages, one override advisory, and one blocking defect-lint failure. The
blocking witness was an accepted negative `sample_index`; the advisory noted that
multi-axis incompatibility errors did not identify the axes structurally.

The first post-edit battery is intentionally retained at
`checks/after/checks/3ab9aab86992_after_battery_summary.json`. Its 9 green / 3
failed result caught the first schedule's median object-count regression, the
undeclared schedule-enumeration requirement, and a transient Racket authority
startup failure. That evidence drove the final two-dense/two-incomplete schedule
rather than being deleted or relabelled.

The final source-bound battery is
`checks/after-final/checks/3ab9aab86992_after_battery_summary.json`: 12 green,
zero advisory, zero failed, with `--require-rotations-identifiable` and
`--enumerate-schedule-period --schedule-seed 0`. The generator source bound into
that report is `14f3c3a81127c7f65da3bd837ef287021fb5d8cba1c61f65dc76ac8d5c8af384`.

## Production repair

### R1 — strict public call contract

`generate()` now requires literal integer `seed` and `sample_index` values,
rejects booleans, floats, strings, and negative indices, and validates difficulty.
The regression cases cover all of those forms. Exact generator controls remain
observable; unknown keys still fail rather than becoming silent no-ops.

### R2 — structured incompatibilities

Known legal override combinations are represented by
`INCOMPATIBLE_OVERRIDE_COMBINATIONS = []`. When a diagnostic texture conflicts
with another exact axis, the raised `ValueError` now carries an
`incompatible_axes` tuple naming the controls, so the shared override checker and
callers can distinguish a declared incompatibility from an arbitrary failure.

### R3/R4 — rotation-safe teaching without density collapse

The final declared schedule has period four and three required demonstrations:

| Difficulty | Cardinalities before seed rotation |
|---|---|
| easy | `(1, 2, 4, 4)` |
| medium / unspecified | `(2, 3, 4, 4)` |
| hard | `(3, 3, 4, 4)` |

`seed % 4` rotates the sequence, and `sample_index` selects the slot. Every
three-of-four holdout includes an incomplete orientation set, which refutes the
finite declared `complete_all_corners` rival regardless of query position. The
first attempted schedule used only one dense slot; it passed the local rotation
logic but failed the distribution gate because `generate(seed, seed)` had median
one object. The final two-dense schedule preserves the same rival-refutation
property while restoring the gate-style median to at least three. An explicit
`n_corners` request always overrides the schedule.

`LESSON_COMPETITORS` is now explicit, and `lesson_identifiable()` validates the
materialized demos/query before testing each declared rival. This is a finite
contract against named hypotheses, not a proof of unique induction against every
possible rule.

## Verification evidence

- Portable selected-task suite: `checks/task-tests-final-source/result.json`,
  118 passed, zero failed/errors/skipped, including live Racket execution of both
  parametric programs.
- Final strict battery: `checks/after-final/`, 12/12 green with rule, profile,
  distribution, override, semantic, grammar, and authority stages.
- Production census: `checks/lesson-census-final.summary.json` plus compressed
  full report `checks/lesson-census-final.json.gz`; 300 materialized lessons,
  1,200 pairs/rotations/unique inputs, zero ambiguity or hook/scoring errors.
- Exhaustive declared period: `checks/schedule-census-final.summary.json` and
  `checks/schedule-census-final.json`; 12 starts and 48 rotations, all clear for
  the declared rival at seed 0.
- Shortcut/Racket witness: `checks/main-shortcut-final.json`; all five cases
  validator-lawful, exact expected outputs matched, and the rival disagreed on
  the retained incomplete-corner case.
- Fresh delta replay: `checks/replay-candidate/replay.json` applied all eight changed paths in a 367-file declared-runtime closure from the 90,295-file source packet and reproduced the final generator SHA; `checks/replay-candidate/fresh-test-summary.json` then records 118/118 tests passing in that checkout.

## Racket authority

No canonical or selected Racket program was changed. The final authority stage
reports `selected_synchronized_archival_divergent`: the selected authority is
synchronized and execution parity passes, while the pre-existing archival raw
source remains divergent and untouched. This return does not upgrade catalog or
training approval.

## Parametric-rule assessment (P1)

The isolated prototype in `workspace/parametric/prototype.py` introduces one
episode-level parameter, `corner_basis`:

- `elbow` (default) is byte-for-byte the canonical exact Racket program, SHA
  `c83accbef454499a8c9af94eaf34ddd2d50551e7312ed9a0360c34a00985fd89`.
- `missing` maps the absent corner of each tiny L's 2×2 bounding box to the
  enlarged output corner, exact Racket program SHA
  `104cbc0147fc9f4750c0d5b00e7ca60bbf3321140393ab8e763f1b0b3eb0be31`.

`checks/parametric-final-source/evidence.json` contains two complete deterministic
episodes (seeds 7301 and 7303), each with three demonstrations and one query,
exact program text/hashes, redacted public challenges, private labels, and zero
surviving declared parameter-rival findings. The evidence covers two episodes
and one opposite-setting rival only; four-orientation same-color scenes can make
the settings answer-equivalent. The prototype is not wired into production,
canonical authority, catalog approval, or training admission.

## Shortcut answer (Q1)

`complete_all_corners` fits all canonical demonstrations because each canonical
input contains all four orientations. The selected generator emits lawful
incomplete orientation sets; the retained `generate(0, 0, canvas_size=7,
bg_color=8, n_corners=1, palette_size=1)` case makes the canonical Racket output
draw only the top-right border L while the rival fills all four corners. Full
arrays and checking method are in `QUESTION_ANSWER.md` and
`checks/main-shortcut-final.json`.

## Solve records

The independent blind task `865e48425b05` finished after two visible-only
attempts with no earlier exposure and no reference consultation; all three
visible examples passed, while query labels remain masked. The exposed
post-repair solve for `3ab9aab86992` is bound to final generator SHA `14f3c3a81127c7f65da3bd837ef287021fb5d8cba1c61f65dc76ac8d5c8af384`;
its first component-based hypothesis passed all three visible examples, earlier
rule exposure is declared `yes`, no reference was consulted during solving, and
query correctness remains unknown. See `solve-blind/summary.json` and
`solve/summary.json`.

## Audit-only work

`AUDIT.md` records two reproduced advertised-axis defects. The optional combined
audit preset completed for each target but correctly did not pass: neither target
has task-local tests, and neither declares the strict semantic contract required
by the preset. Those failures do not weaken the concrete 20-seed axis probes and
were not converted into repair claims.

## Failed iterations and limitations

Intermediate failed batteries and the initial staged mixed-source import error
are retained under `checks/after/` and `checks/task-tests/`. The final tests avoid
cross-tree package reuse, but this was a test portability repair rather than a
change to shared tooling.
A full 90,295-file replay attempt was also controller-killed after extraction and remains `status: running` in `checks/replay-candidate/full-replay-interrupted.json`; the supported runtime-closure replay completed and is explicitly reported as partial scope.
The final whole-change author self-review is retained at `checks/self-review-final.md`; no subagent reviewer was available, so it explicitly records that limitation.

Self-review for new shortcuts found that seed-rotating a deterministic period can
itself expose cardinality phase, but the phase is nonsemantic, all four query
rotations retain an incomplete witness, and explicit cardinality pins take
precedence. Self-review for distribution restriction found the initial one-dense
schedule was too sparse; the final two-dense schedule restores canonical-like
object density while retaining 1–3-object support, though it does not establish
uniform coverage of all legal packings or universal identifiability.

## Acceptance

**Acceptance: routine.** The selected production source, focused tests, strict
battery, lesson evidence, exact shortcut witness, solve binding, and authority
identity agree on SHA `14f3c3a81127c7f65da3bd837ef287021fb5d8cba1c61f65dc76ac8d5c8af384`. Remaining caveats concern finite hypothesis scope
and a separately labelled unapproved prototype, not a known blocker in the
selected repair.
