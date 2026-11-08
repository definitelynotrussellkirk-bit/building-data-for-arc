# Working notes: 3dc5b297cfa2

## Current source and intended rule

- Review assignment: `review-1d85d537b316e701` (2026-10-20).
- Generator version: `3.1.1`.
- Final generator SHA-256: `bba8a758eeed3d632897a59bc11f4cc91199364ba7cd2a16c4c69a1bedf9c962`.
- Canonical rule pin: `RULE_HASH = "69b3b2d19383"`; the selected Racket authority was not changed.
- Grammar: one 4-connected two-color shape on a unique nonzero modal background.
- Transformation: swap the two shape colors; split at the floor midpoint of the shape bbox; move only the top half right. Use full bbox width normally, but when black is a shape color use the horizontal span of the nonblack cells.

## Prior lead and reproduced teaching defect

Retained audit `review-1a8df232040f97a4:v0001` was used as a lead and then covered by new task-local regression tests. Its audited source was SHA-256 `ba3a4697cb2d3636bfc77d56a450afc3375f7b21f729667f665c791c07b05c76`.

The prior four-slot schedule could produce a three-pair branch pattern `[nonblack, black, nonblack]`. If the middle black pair became the query, the two remaining demonstrations both used the ordinary full-bbox shift. The declared `always_full_bbox_shift` rival therefore fit every demonstration but differed on the black query. The exact retained case uses easy-band seed `2133068724`, start sample index `1`, pair indices `[1,2,3]`, and held-out query index `1`. A compact current review record is at `counterexamples/review-1d85d537b316e701/rotated_query_hidden_black_branch.json`; the original grids and Racket receipt remain in the retained audit assets.

## Reversed schedule decision

**Prior choice.** Four slots alternated black/nonblack profiles and were sufficient for ordered two-demo windows, but not for every possible query rotation.

**Current choice.** Six slots use:

1. `canonical_black_8x5`
2. `broad_black`
3. `canonical_nonblack_8x5`
4. `canonical_black_8x5`
5. `broad_black`
6. `canonical_nonblack_6x7`

This `B,B,N,B,B,N` cycle keeps at least one black-branch demonstration after any one holdout from every cyclic three-pair window while preserving all linked canonical profiles. `workspace/rotation_probe.py` exhausts all six starts and all three query positions for finite deterministic seeds. Final evidence: 180 lessons, 540 rotations, zero ambiguity, and minimum one retained black demo (`checks/rotation-probe.json`). The independent production census materialized 300 lessons and 900 rotations with zero declared-rival ambiguity (`checks/lesson-census.summary.json`).

## Strict public call boundary

An intermediate after battery found 48 strict-scalar warnings: bools, floats, strings, and negative seed/sample-index values were accepted. `generate` and `schedule_profile` now share `_validate_call`, requiring literal nonnegative integers and one of `None|easy|medium|hard`. `tests/test_call_contract.py` first reproduced 20 representative failures and now passes. The failed intermediate battery is retained under `checks/after-pre-strict-scalars/`.

## Parametric family prototype

The selected canonical generator remains unchanged in rule semantics. A separate proposed prototype under `workspace/parametric/` varies two episode-level parameters:

- `moving_half = top | bottom` (default/canonical: `top`)
- `direction = right | left` (default/canonical: `right`)

The prototype preserves the object roles, bbox split, color swap, and black-specific shift-magnitude branch. It recenters inputs so every setting is unclipped. `top + right` emits the canonical Racket program byte-for-byte. Four deterministic episodes cover all four settings, each with three demonstrations and one query; 70 Racket executions agreed with an independent Python oracle, and every episode separates its chosen setting from the other three. Evidence: `checks/parametric/split-motion-v1/`. These variants are proposed only; no approval or training-value claim is made.

## Verification and limits

- Final battery: all 12 stages green on the final source.
- Portable selected-task tests: 36/36 passed.
- Production lesson census: 300/300 materialized, 900 pairs, 814 unique inputs, zero production ambiguity, zero rotated-query ambiguity, and zero materialization/scoring errors.
- Rotation-period probe: all six starts × three bands × ten seeds; 540/540 query rotations identifiable against the declared competitors.
- Post-repair visible-only solve: revision 1 passed all three visible examples; earlier rule exposure was recorded honestly.
- The initial before battery was controller-interrupted after its child lint log had already reported zero errors/warnings; it is retained as interrupted evidence, not counted as a baseline aggregate pass.

Finite rival checks do not prove universal induction. The prototype covers four settings and a centered canonical-grammar subset only. Passing checks do not approve the canonical generator or proposed variants for training. No selected-generator blocker remains open in this review.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-1a8df232040f97a4:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `ba3a4697cb2d3636bfc77d56a450afc3375f7b21f729667f665c791c07b05c76`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit resolution onbba8a758: six-slot B,B,N,B,B,N schedule retains black-branch evidence after each single query holdout, replacing four-slot N,B,N failure. Reviewer36portable tests,12/12 battery,300two-demo/query lessons/900required rotations and180cyclic-start lessons/540rotations across6starts/3bands/10seeds each show0ambiguity. Old exactsource/rotationwitness retained; canonical Racketunchanged. Finite declared-rival/default assembly qualification, no owner battery rerun or universal induction.

### Assessment or prior finding

## 3dc5b297cfa2

**Reproduced rotated-query teaching defect; ordinary production order remains
clean and the audit target was left unchanged.** The audited generator is
SHA-256 `ba3a4697cb2d3636bfc77d56a450afc3375f7b21f729667f665c791c07b05c76`
and declares rule hash `69b3b2d19383`.

The generator passes standalone lint, all 9 task tests, and the strict semantic
stage. Even that semantic log reports 6 ambiguous rotations among its 36
rotation diagnostics. A larger source-bound production census materialized 150
lessons (450 pairs, 435 unique inputs): all 150 ordinary ordered lessons were
identifiable, but 75 of 450 held-out query rotations were ambiguous
(`checks/audit/3dc5b297cfa2/lesson-census-summary.json`).

Every failure has the same mechanism. A three-pair window has branch pattern
`[nonblack, black, nonblack]`; when the black middle pair is the query, both
remaining demonstrations use the ordinary full-bounding-box shift. Therefore
the declared `always_full_bbox_shift` rival fits both demonstrations but predicts
a different answer for the black query, whose correct shift is the narrower
nonblack span.

The retained exact case is easy-band seed `2133068724`, start sample index 1,
pair sample indices `[1,2,3]`, query index 1. Both nonblack demos have
`rival_matches_labeled_output=true`; the black query has bbox width 4 but rule
shift 2. The query passes the target validator, belongs to the documented
production generator domain, and the authoritative Racket output differs from
the rival output. Full grid, outputs, hashes, command, and working directory are
in `checks/audit/3dc5b297cfa2/rotation_counterexample.json`, with the supported
Racket application receipt in `checks/audit/3dc5b297cfa2/racket.json`.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-1a8df232040f97a4-v0001/audit_assets.json), manifest SHA-256 `7b3883cc3cb2eb6914c8d58291c68ebf479712a3203ad7ead1d28c04d6b1aac9`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `bba8a758eeed3d632897a59bc11f4cc91199364ba7cd2a16c4c69a1bedf9c962`.

# Decisions for `review-1d85d537b316e701`

## D1 — Preserve the canonical transformation and authority

**Choice.** Keep the selected Racket authority and `RULE_HASH = "69b3b2d19383"` unchanged.

**Reason.** The retained finding concerns lesson composition, not incorrect labels. All six canonical pairs, rule smoke, Racket lint, and authority synchronization pass on the final source.

**Rejected alternative.** Removing the black-specific shift branch would make the old ambiguous lesson easier to teach but would contradict canonical examples. Changing the authority to accommodate a curriculum defect would repair the wrong layer.

## D2 — Repair the schedule rather than increase demonstration count

**Prior choice.** The v3.0.0 four-slot cycle was `canonical black 8×5`, `canonical nonblack 8×5`, `broad black`, `canonical nonblack 6×7`. It guaranteed branch coverage for ordinary consecutive two-demo windows but not after arbitrary query rotation.

**Current choice.** Use the six-slot cycle `B,B,N,B,B,N`, concretely:

1. `canonical_black_8x5`
2. `broad_black`
3. `canonical_nonblack_8x5`
4. `canonical_black_8x5`
5. `broad_black`
6. `canonical_nonblack_6x7`

**Reason.** A lesson still contains only two demonstrations plus one query, but any single holdout from a cyclic three-pair window leaves at least one black-branch demonstration. This directly kills the retained `always_full_bbox_shift` rival while preserving all three linked canonical profiles and broad input support.

**Rejected alternatives.** Raising `EXAMPLES_NEEDED` from two to three would increase training cost and was unnecessary. Random resampling until a black demo appears would obscure determinism and could still fail under rotated queries. Forbidding query rotation would preserve the old ordered curriculum but would leave a known portability hazard for downstream lesson assembly.

**Evidence.** `tests/test_rotation_curriculum.py`, `workspace/rotation_probe.py`, `checks/rotation-probe.json`, and `checks/lesson-census.summary.json`.

## D3 — Require the same strict call boundary for schedule and generation

**Choice.** Add `_validate_call` and use it in both `schedule_profile` and `generate`: seed and sample index must be literal nonnegative integers, and difficulty must be exactly `None`, `easy`, `medium`, or `hard`.

**Reason.** The first after battery found 48 strict-scalar warnings. Accepting bools, floats, strings, and negative values made deterministic replay and schedule reasoning less reliable.

**Rejected alternatives.** Coercing values with `int()` would silently merge distinct caller inputs. Validating only `generate` would leave `schedule_profile` inconsistent with the actual public generation boundary.

**Evidence.** `tests/test_call_contract.py`; failed intermediate battery `checks/after-pre-strict-scalars/`; final green defect lint in `checks/after/`.

## D4 — Keep exact generator axes unchanged

**Choice.** Retain the six exact controls already established by the previous v3 repair: `grid_h`, `grid_w`, `bbox_h`, `bbox_w`, `background_color`, and `black_shape`.

**Reason.** The current defect did not arise from input geometry. All controls remain observable and honored, and the final override stage passed. Changing the geometry surface during a curriculum repair would add risk without addressing the retained counterexample.

**Rejected alternatives.** Adding an explicit schedule/branch override was unnecessary because `sample_index` already selects deterministic profiles; exposing curriculum internals as a visual axis would confuse generation controls with lesson assembly.

## D5 — Build a rotation-complete reusable probe

**Choice.** Add `workspace/rotation_probe.py`, which discovers the final schedule and declared competitors from the selected module, enumerates every start and every one-pair holdout, and records source/probe hashes.

**Reason.** A random lesson census covers many examples but does not exhaust a small cyclic schedule. The retained defect was a specific start/holdout interaction, so complete period coverage is cheap and more diagnostic.

**Scope.** The final report covers six starts × three bands × ten deterministic seeds and all three query positions: 180 lessons and 540 rotations. It tests declared competitors only and does not prove uniqueness against unnamed hypotheses.

## D6 — Choose two small episode-level rule parameters for the prototype

**Choice.** Prototype `moving_half = top|bottom` and `direction = right|left`, chosen once per episode. Defaults are `top` and `right`.

**Reason.** Both parameters preserve the original family: detect the same object, use the same bbox midpoint, swap the same two colors, keep the same black/nonblack shift-magnitude rule, and move exactly one half horizontally. They change a single relational choice each and are easy to demonstrate visually.

**Rejected alternatives.** Varying split location would alter the central reasoning boundary and risk degenerate small halves. Varying shift magnitude would collide with the canonical black-specific exception. Vertical motion would require a larger layout redesign and was unnecessary for a first family extension.

## D7 — Preserve canonical bytes for the default prototype setting

**Choice.** `materialize_program("top", "right")` returns the selected canonical Racket program byte-for-byte; other settings are separately materialized variants.

**Reason.** This makes the canonical default auditable and prevents a prototype helper from silently rewriting the approved authority text.

**Evidence.** `tests/test_parametric_motion.py` and `checks/parametric/split-motion-v1/report.json`.

## D8 — Recenter prototype inputs rather than clip or reject settings

**Choice.** Generate the prototype's examples in a 24-column centered canvas with enough margin for both left and right motion.

**Reason.** Parameters are chosen once per episode; every chosen rule must be executable on every demo and query. Recentring preserves visible object semantics without clipping.

**Rejected alternatives.** Clipping would change the rule. Rejection sampling after choosing a parameter would complicate reproducibility. Using the full selected-generator distribution would include right-biased placements unsuitable for left motion.

**Limit.** The prototype demonstrates a centered canonical-grammar subset, not the selected generator's complete support.

## D9 — Fix the prototype executor at the application boundary

**Observed failure.** The first evidence run evaluated the lambda-valued rule but did not apply it to the bound grid, so Racket returned a procedure rather than a transformed grid.

**Root cause.** The wrapper treated the canonical `(rule! (lambda ...))` form as an expression result instead of extracting the procedure body and invoking it with the episode input.

**Choice.** Strip the outer `rule!` wrapper, evaluate the lambda, and apply that procedure to the bound grid. Keep rule semantics unchanged.

**Evidence.** Focused prototype tests and the final 70-execution report. The failed diagnostic was not promoted as successful evidence.

## D10 — Keep the proposal outside the production API

**Choice.** Store the parametric implementation only under `workspace/parametric/`; do not add variant controls to `generator.py` or change catalog approval state.

**Reason.** The assignment asks for a runnable family assessment, not automatic selection. Separating it prevents proposed variants from contaminating canonical generation or being mistaken for approved training data.

## D11 — Treat controller interruptions as interruptions

**Choice.** Preserve the initial before battery and audit-stage interruptions, but do not count them as passes or failures of generator semantics.

**Reason.** The before child lint log says all checks passed, while the controller receipt says interrupted. Evidence before claims requires the aggregate to remain interrupted. The final source has an independent completed after battery.

## D12 — Leave adversarial audit targets unchanged

**Choice.** Do not edit `df74e338b4f5` or `bf8e1d3e9c4c`.

**Reason.** The duties separate peer audits from the selected repair. `AUDIT.md` records a clean bounded review for the first and a source-bound exact-control/lint defect for the second, with reproduction files under `checks/audit/`.
