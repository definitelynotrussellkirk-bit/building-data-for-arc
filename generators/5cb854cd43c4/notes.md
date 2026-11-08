# Working notes: 5cb854cd43c4

## 2026-10-03 review `review-6f014ab487c35469`

### Baseline and lead

The retained note `GNOTE-000092` was used as a lead, not as a measurement of this packet. It accurately identified equal-size and repeated-color inputs as authority-valid but said version 4 deliberately excluded them because the public episode did not disambiguate those cases. The packet's fresh before battery confirmed version 4 itself was healthy on syntax, generation, overrides, and authority, but had no executable semantic contract: 11 stages green and `semantic_gate` advisory-only (`checks/before/`).

A direct canonical-pair check established the actual teaching defect:

- every public pair uses a distinct color for each component, so a solver that merges disconnected components by color fits all public pairs;
- every public pair has strictly different component sizes, so the ascending-color tie-break is never exercised.

### Version 5 design

The rule and public control surface were preserved. Version 5 adds no new advertised axis. It uses `sample_index % 3` to select:

1. `split_color_witness`: a strict varied-size scene with two disconnected objects sharing a color;
2. `tie_break_witness`: a varied scene with at least one equal-size pair using distinct colors;
3. `ordinary`: a canonical-size, distinct-color scene.

Three consecutive generated demonstrations therefore contain both required witnesses regardless of the starting residue. Explicit `size_regime=canonical` and `size_regime=varied` continue to be observable through the historical two-axis contract. The 6x6 `(3, 3)` tie tuple remains excluded because the frozen legacy negative fixture pins it as unsupported; other 6x6 equal-size pairs teach the same tie-break.

The semantic contract names and executes both witnesses and both rivals. `lesson_identifiable` checks demonstrations against the true mirror and rejects lessons in which a declared competitor still determines a different query answer.

### Verification and tools

- Final source SHA-256: `f36f679fc10a563b313eea278ac185dea636c3f96dfdbbd5ea7dfcfa5c9cee1c`.
- Frozen fixture SHA-256 remained `fb62c035c3c2853415603c494bb2d5ab0aa6637aa4ae88504789dfc2c4a23e0c`.
- Final battery: 12/12 green (`checks/after/`).
- Portable selected-task suite: 11/11 passed via `workspace/run_task_tests.py`.
- `workspace/lesson_probe.py` replays the semantic gate's exact pinned plan with canonical Racket outputs. Its 300-lesson report (100 per band) found 400/400 unique inputs per band, zero Python-mirror/Racket disagreements, and both declared rivals refuted by demonstrations in all 300 lessons (`checks/lesson_probe_300.json`).
- Exact shortcut counterexample and authoritative output: `checks/shortcut_counterexample.json`.

One retained failed iteration is intentional evidence: the first repaired source passed 11 stages but the generic linter warned that local variables named `objects` echoed a Racket primitive. Renaming those locals, without changing behavior, produced the final all-green source (`checks/after-failed-lint/`).

### Limits

This curriculum is deliberately bounded to the three declared canvases, two or three components, enumerated size tuples, same-color 4-connectivity, and a limited repeated-color pattern. The 300-lesson probe shows that the two strongest canonical-fitting rivals are eliminated on this generated domain; it is not a proof of universal induction or coverage of every imaginable shortcut.
## Current reviewer considerations

Source SHA-256: `f36f679fc10a563b313eea278ac185dea636c3f96dfdbbd5ea7dfcfa5c9cee1c`.

# Decisions for 5cb854cd43c4

## D1 — Preserve the canonical authority

**Choice.** Leave the Racket rule unchanged and retain `RULE_HASH = e1a351c73552`.

**Rationale.** Fresh rule-smoke and authority-sync checks showed that the selected authority is synchronized and executable. The observed defect was not wrong output semantics; it was that version 4 never taught two authority-valid cases. Editing the rule would have expanded risk without addressing the actual cause.

**Alternatives considered.** Narrow the rule to distinct-color/strict-size scenes, or special-case ties/repeated colors. Both were rejected because they would make the authority disagree with valid inputs and with the existing broad Python oracle.

**Probe/evidence.** Before and after `rule_smoke`, `authority_sync`, and `checks/shortcut_counterexample/racket.json`.

**Failure mode/limit.** The generator still depends on the canonical rule's per-object 4-connectivity and ascending-color tie-break; a future authority change requires a fresh source-sync and semantic replay.

## D2 — Keep the historical exact-axis surface

**Choice.** Retain only `scene_profile` and `size_regime`; do not add `color_pattern`, `schedule_profile`, or `tie_kind` as public overrides.

**Rationale.** The frozen fixture and downstream tooling already define an exact two-axis contract. The repair needed a teaching schedule, not a new caller-facing control. Both new witness branches can be represented honestly as `size_regime="varied"`, and `observe_overrides` still recovers every advertised axis.

**Alternatives considered.** Add a public `color_pattern` or `lesson_role` axis. Rejected because it would enlarge the contract, require new mixed-override semantics, and risk breaking the frozen fixture for no training benefit. Remove the existing `size_regime` axis. Rejected because it is observable and used by retained tests.

**Probe/evidence.** Final override stage is green; the unchanged frozen fixture hash is `fb62c035c3c2853415603c494bb2d5ab0aa6637aa4ae88504789dfc2c4a23e0c`.

**Failure mode/limit.** Callers cannot request one specific witness branch directly. The task-local `schedule_profile()` hook exposes the deterministic branch for diagnostics without advertising it as an exact generation axis.

## D3 — Use a deterministic three-step lesson schedule

**Choice.** Select `split_color_witness`, `tie_break_witness`, and `ordinary` by `sample_index % 3`.

**Rationale.** A frequency-only random mixture can pass a 600-draw census while still produce individual lessons with no disambiguating example. With three demonstrations per lesson, a three-residue cycle guarantees both shortcut-killing witnesses in every consecutive window, independent of starting residue.

**Alternatives considered.** Draw branches independently at random; rejected because nonzero global witness frequency is not a lesson-level guarantee. Put both phenomena into one overloaded example; rejected because separate examples are easier to interpret and test. Emit only witnesses; rejected because one ordinary canonical-profile draw per cycle preserves public-like coverage.

**Probe/evidence.** `test_every_default_three_demo_window_refutes_both_shortcuts`, the final semantic gate (12/12 lessons identifiable), and `checks/lesson_probe_300.json` (300/300 lessons refute both rivals in their demonstrations).

**Failure mode/limit.** The guarantee assumes `EXAMPLES_NEEDED = 3` and consecutive sample indices. A future lesson assembler that skips indices or changes demonstration count must replay all cyclic starts or revise the schedule.

## D4 — Bound repeated colors to strict-size scenes

**Choice.** On the split-color branch, use a strict descending varied-size tuple and repeat exactly one color across two disconnected components.

**Rationale.** This isolates the intended distinction—component identity versus color aggregation—without simultaneously invoking the size-tie rule. It preserves three nonzero components on the public three-object canvases and two on the public two-object canvas.

**Alternatives considered.** Repeat colors on canonical tuples; viable semantically, but rejected to keep the canonical branch byte-for-byte aligned with its prior interpretation. Allow every component to share one color; rejected because it reduces palette diversity and creates a less natural, more easily memorized witness. Use diagonal-only separation; rejected because it introduces a second connectivity ambiguity.

**Probe/evidence.** `split_same_color_components`, the `merge_disconnected_same_color` rival, and the exact Racket-backed example in `checks/shortcut_counterexample.json`.

**Failure mode/limit.** The branch teaches one repeated-color pattern only. It does not prove behavior for arbitrary numbers of same-color components or alternative connectivity conventions.

## D5 — Add calibrated equal-size tuples, with one frozen exclusion

**Choice.** Add enumerated equal-size, distinct-color tuples to the existing varied regime. Keep 6x6 `(3, 3)` excluded and use `(2, 2)`, `(4, 4)`, or `(5, 5)` instead.

**Rationale.** Equal-size objects are the smallest direct witness for the ascending-color tie-break. Enumeration preserves placement reliability and the existing calibrated canvas/object counts. The 6x6 `(3, 3)` tuple remains excluded because the immutable legacy negative fixture explicitly expects that mutation to fail; alternative equal pairs teach the same semantic fact.

**Alternatives considered.** Permit arbitrary equal sizes; rejected because unbounded placement combinations would weaken exact-domain validation and add avoidable construction failures. Patch the frozen fixture; prohibited and rejected. Rely on a verbal tie-break declaration without examples; rejected because the canonical demonstrations do not exercise it.

**Probe/evidence.** `equal_size_color_tie`, `larger_color_first_on_ties`, the frozen fixture, and 100 lessons per band in `checks/lesson_probe_300.json`.

**Failure mode/limit.** Only the listed tie tuples are in the generated domain. The evidence supports the tie-break on that bounded set, not every possible object size/canvas.

## D6 — Make source-bound verification reusable

**Choice.** Add `workspace/run_task_tests.py` and `workspace/lesson_probe.py`.

**Rationale.** The packet layout cannot run the retained task tests directly because the tests expect the installed `puzzle_generators/per_puzzle` and `data` layout. The test runner stages exact current source/test bytes into an ephemeral portable namespace and prints hashes. The lesson probe imports the current source bytes, reuses the semantic gate's pinned sampler, and obtains every output from one persistent canonical Racket bridge.

**Alternatives considered.** Rewrite the frozen fixture's imports; prohibited. Test only the new file; rejected because it would omit the retained contract. Use the Python mirror as the probe authority; rejected because it would not detect mirror/authority drift. Copy the full runtime into the task workspace; rejected as unnecessary and too large.

**Probe/evidence.** Portable suite 11/11, generator source hash `f36f679fc10a563b313eea278ac185dea636c3f96dfdbbd5ea7dfcfa5c9cee1c`, and zero mirror/Racket disagreements across 1,200 probe pairs.

**Failure mode/limit.** Both helpers depend on private-but-retained packet modules and paths. They are task-local review tools, not a promised public API.

## D7 — Retain the failed lint iteration

**Choice.** Keep `checks/after-failed-lint/` and fix only the warned local identifiers.

**Rationale.** The first repair was functionally green on 11 stages but failed the blocking lint policy because two local names were `objects`, a word also used by a Racket primitive. Renaming them to `components`/`color_groups` removed the warning without semantic change. Preserving the failed evidence makes the iteration and source transition auditable.

**Alternatives considered.** Suppress the warning or omit the failed run; rejected because the assignment requires no blocking warnings and asks that failed iterations be retained. Refactor the rival logic; rejected because no behavior defect was present.

**Probe/evidence.** `checks/after-failed-lint/checks/5cb854cd43c4_after_lint.log`, standalone lint, then final 12/12 battery.

**Failure mode/limit.** This was a generic linter false alarm rather than a task defect; the shared-tool feedback is recorded separately in `FEEDBACK_TO_CODEX.md`.
