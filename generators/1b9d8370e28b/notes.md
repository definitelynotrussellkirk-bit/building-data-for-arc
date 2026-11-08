# Current notes: 1b9d8370e28b


## Current return: native promotion readiness (`review-715375683a51272b`)

The production generator and selected canonical rule are unchanged. This return
adds the missing task-local native promotion surface for the retained
`cyan_anchor=left|right` prototype:

- `workspace/parametric/adapter.py` reuses the exact adjacent prototype and
  exports `program(settings)` plus `generate(seed, settings, demos, queries)`;
- `workspace/parametric/promotion.json` declares canonical default `left` and
  independent 1–32 demo/query limits;
- matched inputs are setting-independent, duplicate draws are skipped under a
  deterministic 4,096-candidate cap, and all public controls reject coercive
  scalar types;
- the default program remains byte-exact SHA-256
  `224da981d08839808cf57b4501b36c8cbf96e6a9437a50a98605af78c050bbf8`.

Scoped qualification exercised both settings on seeds 0 and 17 with three
demonstrations and four distinct queries. Protected Racket performed 40
executions; each job retained only its selected setting after demonstrations,
and every query label matched. The focused adapter suite passed 20 tests,
including 32+32 distinct inputs and a forced duplicate-retry edge case; the
combined adapter/retained-prototype suite passed 38 tests. This prepares exact
bytes for owner qualification review only. Variant acceptance, production API
use, training admission, and measured learning benefit remain unresolved owner
or trainer decisions.

## Selected canonical task

The grid has one straight split between cyan (8) and blue (1) backgrounds, with
red (2) cells overlaid in both regions. For each row and each region, erase the
original red positions while preserving that row's red count. Compact those red
cells to the left edge of a cyan region and the right edge of a blue region.
The selected canonical Racket rule remains unchanged and is pinned by
`RULE_HASH = "c5b820b4a73f"`.

Selected generator version: `3.0.1`.
Final generator SHA-256:
`8ae90d9e93bb533b943d720f02ba8418def0f06c346902bbed75ac1fc59bfa1f`.

No separate prior-return ZIP was used as evidence. Existing task notes and the
review index were read only as leads; all current claims below were remeasured
on the packet's pinned source and retained evidence.

## Production distribution and teaching contract

Production generation remains the reviewed v3 distribution: 9–15 by 9–15
boards, horizontal or vertical splits, either top/left background color, and
3–5 separated red components. Every ordinary draw includes a connected ragged
component that distinguishes the row-wise rule from the strongest canonical-
fitting shortcut, rigid translation of whole components.

Lessons use **3 demonstrations + 1 query**. The final source-bound census
materialized 300/300 lessons across easy/medium/hard, yielding 1,200 unique
inputs. Ordered production had 0 ambiguous lessons. Holding out each of the
four labelled pairs in turn produced 1,200/1,200 checked query rotations with
0 ambiguities, hook warnings, materialization errors, or scoring errors against
the declared rigid-component rival. This is finite declared-rival evidence, not
a proof against every possible hypothesis.

## Repairs in this return

### Strict request validation

The prior generator delegated scalar handling to coercive infrastructure. It
accepted booleans, floats, and strings for deterministic identity fields and
some axes; certain invalid `tl_color` values failed later as an internal runtime
error. `generate` now validates before any draw:

- `seed` and `sample_index` must be exact integers; booleans are rejected;
- `sample_index` must be nonnegative;
- `difficulty` is limited to `None`, `easy`, `medium`, or `hard`;
- only the four declared override keys are accepted;
- `grid_h`/`grid_w`, `split_axis`, and `tl_color` use strict type/value checks;
- explicit `None` overrides remain equivalent to omission.

Focused regressions are in `tests/test_contract_repairs.py`.

### Selected authority synchronization

Two task authority JSONs had behavior-equivalent but textually stale selected
`racket_target.target_code`. Their selected `target_code` fields now exactly
match the canonical `program_solution`. The archival `raw_code` fields were
**not changed** and remain byte-identical, SHA-256
`2a341050fb24c1c96e87cbd385e218052904360727db710e04e3b627124fbe96`.
Metadata now states that selected code is canonical while archival raw requires
execution-parity preservation. Canonical behavior did not change.

### Proposed parametric extension

`workspace/parametric/` contains a separate, runnable, unapproved prototype with
one episode-level parameter:

- `cyan_anchor=left` — canonical/default: cyan compacts left, blue right;
- `cyan_anchor=right` — alternative: cyan compacts right, blue left.

The setting is selected once per deterministic episode. Each episode has three
demonstrations and one query, and all retained labels are executed by protected
Racket. Evidence for seeds 0 and 1 exercises both settings, checks byte-exact
canonical replay for the default, and shows each alternative is refuted by all
three demonstrations when it is not the selected setting. This prototype is
not integrated into production and does not imply variant approval.

## Verification state

- Before battery on the pinned v3.0.0 source: 10/12 green; `defect_lint` and
  `authority_sync` failed.
- Final v3.0.1 battery: 12/12 green.
- Portable selected-task tests: 60 passed, 0 failed/errors/skipped.
- Final rigid-rival probe: 6/6 canonical pairs fit the shortcut; 1,200/1,200
  generated pairs contain a witness and disagree; every 3-demo lesson refutes it.
- Post-repair visible-only solve: one revision, all 3 visible examples passed;
  earlier rule exposure was declared `yes`, reference consultation `no`.

## Known limits and open status

The production rule and distribution were intentionally not broadened in this
return because the complete baseline semantic/distribution battery was already
green. The new validator is a call-contract repair, not a new task grammar.
The parametric prototype is bounded to two settings and two retained seeds.
Finite rival and rotation checks do not establish universal identifiability.
No selected-task blocker remains; training admission and variant approval are
unchanged and remain maintainer decisions.

## Current owner source and evidence limits

Accepted3.0.1 strict pre-draw scalar checks and selected-only authority replacement with exact unchanged canonical bytes. This selected synchronization changes equivalent runtime spelling and selected/archival role metadata,not merely whitespace;archival raw_code hashes remain2a341050... and unrelated JSON unchanged. Execution parity remains reviewer-reported. Reviewer12/12 battery,60 portable tests,300 production3-demo lessons/1200 rotations clean against declared rigid-components rival. cyan_anchor left/right prototype has two complete3-demo/1-query episodes,exact canonical default and executed Racket labels. Owner replaced ordinal public names and retained actual export from passing focused tests. No new canonical rule,production parameter API,variant approval,training admission or owner full battery rerun.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-04a4310f116a008f:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `b65e363641ba8592c2e3ba088eede64bb732542a43969f1bafe220dce05fd521`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit bounded no_issue for old rigid-component audit:9 tests and300 lessons/1200 witness pairs were clean. Current strict-scalar/selected-text repair is separate;no universal clearance.

### Assessment or prior finding

## 1b9d8370e28b

**Classification: No issue found. Target left unchanged.**

I checked generator SHA-256 `b65e363641ba8592c2e3ba088eede64bb732542a43969f1bafe220dce05fd521` against its focused task suite and its declared canonical shortcut / lesson competitor, `rigid_components`.

- Focused source-bound tests: `9/9` passed (`checks/audit/1b9d8370e28b-task-tests/result.json`).
- The rival fits all 6 usable canonical pairs, so it is a real shortcut worth testing rather than a fabricated negative.
- The source-bound probe then assembled 100 independent lessons in each of easy, medium, and hard: 300 lessons / 1,200 pairs total. Every pair passed the strict validator, every pair contained the declared ragged-component witness, and `rigid_components` disagreed on all 1,200 pairs.
- In all 300 lessons, the three demonstrations refuted the rival; there were 0 cases where it survived demonstrations and changed the query, and 0 `lesson_identifiable` failures.

Evidence: `checks/audit/1b9d8370e28b-rival-probe.json`. The report hashes the exact generator, iterates the generator's own declarations, records the assembly policy, and states its limits. The first direct invocation lacked the packet runtime on `PYTHONPATH`; that environment-only failure is retained at `checks/audit/1b9d8370e28b-rival-probe-attempt1-command.log`, followed by the successful source-identical run.

Scope limit: this finite audit addresses the generator's declared rigid-component rival over the emitted v3.0.0 domain. It is not a proof against every possible shortcut.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-04a4310f116a008f-v0001/audit_assets.json), manifest SHA-256 `e29fb9f590144b752ba669fc2ff5e38d080356bca4299c707dc9c5517176a0ec`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `8ae90d9e93bb533b943d720f02ba8418def0f06c346902bbed75ac1fc59bfa1f`.

# Decisions for `1b9d8370e28b`

## D1 / SEL-01 — validate exact public scalar types before keyed draws

**Decision.** Add one narrow `_validate_request` boundary and reject coercive values before `gen_ctx` or any distribution draw. Require exact `int` for `seed` and `sample_index` (with `bool` rejected), nonnegative sample indices, a documented difficulty string, known override names, and exact override types/ranges. Keep explicit `None` equivalent to omission.

**Rationale.** Seeds and axes are reproducibility controls, not values to reinterpret. Accepting `True`, `9.0`, or `"9"` creates accidental aliases and makes malformed requests look valid. The baseline `defect_lint` reproduced this directly.

**Alternatives rejected.** Coercing numeric-looking values was rejected because it hides caller defects. Validating only after drawing was rejected because an invalid call could already consume deterministic state. Broadly refactoring `gen_ctx` was out of selected-task scope.

**Probe and failure mode.** Focused tests enumerate invalid seed, index, difficulty, and override values and verify omission/`None` equivalence. Future new axes must be added to both `AXES` and `_validate_request`; otherwise unknown-axis rejection is the safe failure mode.

## D2 / SEL-02 — synchronize selected authority text, preserve archival raw text

**Decision.** Replace only the two selected `target_code` fields with the exact canonical program and mark their roles explicitly. Preserve both archival `raw_code` strings byte-for-byte.

**Rationale.** The baseline showed exact-text drift but sampled execution parity. `target_code` is an active selected authority and must be canonical; `raw_code` is provenance and should not be rewritten merely to silence synchronization checks.

**Prior choice and reversal.** The packet began with behaviorally equivalent but divergent selected target text and no archival-divergence role marker. The new choice is exact selected synchronization plus explicit archival preservation, based on the baseline authority diagnostics and the after `authority_sync` pass.

**Alternatives rejected.** Rewriting `raw_code` would destroy retained provenance. Editing the canonical ledger or changing Racket semantics was unnecessary. Leaving the drift as advisory would keep active authorities ambiguous.

**Probe and failure mode.** Regression tests bind the canonical target text and archival SHA-256. `rule_smoke`, `racket_lint`, and `authority_sync` all pass. A future semantic difference between archival raw and canonical selected code must fail execution-parity checks rather than being auto-normalized.

## D3 / SEL-03 — keep canonical production fixed; add `cyan_anchor` only as a task-local prototype

**Decision.** Implement a separate parametric prototype with `cyan_anchor ∈ {left,right}`. `left` is the canonical/default setting; in `right`, cyan compacts right and blue takes the opposite edge. Choose the parameter once per episode from the seed.

**Rationale.** This is a small rule-level change, not a cosmetic palette or sampling change. It preserves split detection, color-conditioned opposing directions, row-wise count conservation, and the original reasoning structure. It also has a clean byte-exact canonical default and a guarded one-fragment alternate Racket program.

**Alternatives rejected.** Varying grid size, split position, object count, or palette would change only inputs. Swapping all colors would be mainly cosmetic. Adding diagonal motion or component-level movement would alter the core family too much. Production integration was rejected because the packet provides no approved parametric runtime API.

**Probe and failure mode.** Seeds 0 and 1 exercise both settings. Every retained episode has three demonstrations and one query; the alternate setting is refuted by all three demonstrations. Exact Racket outputs and source hashes are in `checks/parametric/cyan-anchor-v1/`. The prototype refuses unknown settings, source tampering, invalid seeds, and overwriting an existing evidence directory.

## D4 — retain the production lesson policy at 3 demonstrations + 1 query

**Decision.** Keep the existing production lesson shape and require a ragged connected object in generated scenes so the canonical-fitting rigid-component rival is refuted in the demonstrations.

**Rationale.** The canonical examples use rectangular objects and therefore admit rigid whole-component sliding. A ragged row-offset object exposes the intended row-wise count operation without changing the canonical rule. Three demonstrations are already sufficient in all sampled lessons; no extra examples were needed.

**Alternatives rejected.** Increasing demonstration count would add cost without addressing a missing witness. Allowing witness-free lessons and hoping the query disambiguates was rejected because demonstrations must teach the rule before query prediction. Restricting to one split axis was unnecessary and would weaken coverage.

**Probe and failure mode.** The 300-lesson census checks 100 lessons per band and rotates each of 1,200 pairs into the query position. The task-local rival probe independently reports witness and disagreement counts for all 1,200 pairs. The evidence is finite and covers one declared shortcut; untested rivals remain unknown rather than implicitly disproved.

## D5 — retain `rigid_components` as the principal canonical shortcut and ship a native witness

**Decision.** Keep `rigid_components` in the canonical-shortcut and lesson-competitor declarations. Refresh the source-bound witness against final generator bytes and verify its intended output through native Racket execution.

**Rationale.** It fits all 6 canonical labeled pairs yet differs from row-wise compaction on the generator's ragged components, making it both plausible and diagnostically useful.

**Probe and failure mode.** The exact generated input is seed `910000`, sample index `0`, difficulty `easy`. Native Racket and the Python mirror agree; the rival differs at row 3, columns 8 and 9. Evidence is retained in `counterexamples/current-shortcut/` and `checks/question/1b9d8370e28b-rigid-components/`. Any future sampler change that stops emitting such witnesses should fail the lesson hook and census.

## D6 — audit targets remain evidence-only

**Decision.** Do not edit `c953833a3fba` or `0b999a8ea028`; report their source-hashed findings and counterexamples only.

**Rationale.** The assignment explicitly separates adversarial audits from selected-task repair and states that audits do not approve repairs. Modifying peer targets would violate scope and make the audit evidence non-independent.

**Probe and failure mode.** Both audit source hashes still match `AUDIT_ASSIGNMENT.json`. Reproductions and limitations are in `AUDIT.md` and `checks/audit/`.
