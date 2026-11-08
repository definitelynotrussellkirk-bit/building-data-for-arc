# Working notes: 0a9926d504f3

## 2026-10-04 review `review-863e738ac6bbe039`

Baseline SHA `f80b3c6403b28560c9a823b2cafc171d3bc832ce946edee5b1ea5949d996eafe` failed lint, defect lint, overrides, and authority sync. Root causes were a missing rule pin, band-dependent rejection of advertised dimensions, accepted unknown overrides, structurally ambiguous/overwritten marker roles, no executable semantic curriculum, and two execution-equivalent but text-divergent base authority records.

Final SHA `a5485fd44cb29191d5e497254817d9a1e1f764fd044646063df83b60f1bee9d9` uses constructive geometry, exact override observation, a four-draw semantic schedule, three canonical-fitting rivals, and independent task-local probes. The canonical Racket rule did not change; base records were synchronized to its exact text.

Final evidence:
- battery 12/12 green: `checks/after-final/checks/0a9926d504f3_after_battery_summary.json`
- task tests 243 passed: `checks/task-tests-final/result.json`
- profile floor 20/60 exact: `checks/after-final/checks/0a9926d504f3_after_profile_floor.json`
- lesson census 300/300, zero ambiguity: `checks/lesson-census.json`
- final-source stress probe 1,500/1,500 valid: `checks/stress-probe-final.json`

Known limits: shared-role generation covers top-left only; tied-extrema ordering is intentionally excluded; declared-rival checks are finite and do not establish universal induction.
## Current reviewer considerations

Source SHA-256: `384af5e273f157a3e809dd070b5f985f46753df5c7657e2ce9fbfd7a0c5ab82e`.

# Decisions: `0a9926d504f3` current review

## D10 / R1 — validate call controls without changing generator version

**Choice.** Validate `seed`, `sample_index`, and `difficulty` before `gen_ctx`: exact integers for the first two, nonnegative sample index, and only `None|easy|medium|hard` for difficulty.

**Reason.** The before defect lint reproduced permissive acceptance across all three controls. This was an API-boundary defect, not a distribution or Racket-rule defect.

**Rejected alternatives.** Let `random`/`gen_ctx` fail later (errors would be inconsistent and some malformed values remained silently accepted); coerce values (would hide caller bugs); bump `VERSION` (would unnecessarily change every valid deterministic draw).

**Evidence and limit.** `tests/test_scalar_controls.py`, `checks/before/checks/0a9926d504f3_before_defect_lint.log`, and the all-green final battery. Exact type checks intentionally reject `bool`, despite `bool` being an `int` subclass in Python.

## D11 / P1 — keep `cross_mode` as a proposed, isolated episode parameter

**Choice.** Prototype `cross_mode={plus,horizontal}` under `workspace/parametric/`, select it once per episode, keep `plus` as the canonical/default source, and generate all retained labels with the instantiated Racket rule.

**Reason.** This is the smallest rule variation found that preserves the center/extrema/frame reasoning while changing one visible relation. Three demonstrations distinguish the two settings on all four deterministic lawful fixtures.

**Rejected alternatives.** Frame-precedence variants change conflict semantics and would require additional collision-focused input constraints; changing marker roles or frame extrema would alter the core task rather than parameterize it; adding the parameter to the production generator would incorrectly conflate a proposal with approval.

**Evidence and limit.** `checks/parametric/cross-mode-final/report.json`. Evidence is finite for two modes and four fixtures; it does not establish a production distribution or approval.

## D12 / C1 — retain the ordered four-demonstration curriculum

**Choice.** Support the declared consecutive production ordering only. Do not claim arbitrary query rotation.

**Reason.** In the 300-lesson census, production order had 0/300 ambiguities, while 450/1,500 held-out rotations removed the sole witness for either `center_always_visible` or `preserve_nonrole_markers`. The current downstream assembly preserves the intended order.

**Alternatives considered.** Increase demonstration count or duplicate witnesses so every rotation is identifiable (viable future change, but it raises lesson cost and was not required by the selected assembly); collapse multiple exceptions into every grid (harder to interpret and validate); ignore the rotation result (rejected as an unsupported claim).

**Limit.** Any consumer that may reorder pairs or choose a different query must first repair the schedule and rerun a required-rotation census.

## D13 / P1 — reverse the prototype's initial portable loader choice

**Prior choice.** Reuse `reviewer_support.load_selected_generator` from the prototype.

**New choice.** Resolve the explicit selected source (`GENERATOR_UNDER_TEST` when present, otherwise the task source under the discovered root), hash those bytes, and execute that one module while using the already-selected portable dependency tree.

**Reason.** The first portable task suite imported the frozen fixture's mirrored `puzzle_generators` package, after which `load_selected_generator` rejected those cached modules as belonging to another source tree. That produced three integration failures despite 267 passing tests. The local loader preserves source binding without switching dependency trees; the rerun passed 270/270.

**Evidence.** Failed `checks/task-tests/result.json`; final `checks/task-tests-final/result.json`. This reversal is also the basis of shared-tool feedback F2.

## D14 — preserve audit isolation

The two assigned audit targets were inspected and source-bound counterexamples were built, but neither target was edited. Their findings belong in `AUDIT.md` and do not imply approval or repair.

## D15 — compress the complete census deterministically

The complete census exceeded the return's 25 MiB expanded evidence budget. It is retained as `checks/lesson-census-final.json.gz` using timestamp-free gzip; `checks/lesson-census-final.compression.json` records the original 43,167,692-byte SHA-256, compressed SHA-256, and restore command. The compact summary remains directly readable.
