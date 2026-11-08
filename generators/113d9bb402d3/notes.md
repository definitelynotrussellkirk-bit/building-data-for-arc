# Current notes: `113d9bb402d3`

## Intended rule

Take the bounding rectangle of all cyan (`8`) cells. Recolor only blue (`1`) cells inside that rectangle to green (`3`); preserve cyan cells, zero gaps inside the rectangle, and every cell outside it. Canonical `RULE_HASH` is `3b4315aa79fc`; no Racket authority was changed in review `review-8a556b3bdc6ddb5e`.

## Current lesson policy

- Generator version `3.1.0`; final reviewed SHA-256 `9e8bb87bd4e4fdcac6af02d23c08e8bb676dac96ec4acbb9121de4ade733d3b1`.
- Four demonstrations plus one query are assembled from five consecutive accepted draws.
- Default `zone_coverage` alternates `gapped, complete` with declared period 2; explicit overrides win.
- Any single query holdout leaves a gapped demonstration that refutes `fill_all_noncyan_bbox`.
- Canonical exact profiles occur only on complete slots; conditional prior 0.64 preserves about 0.32 pooled exact support.

## Reversed decision

**Prior:** coverage was independently sampled, allowing a lesson with only complete demonstrations.

**Now:** deterministic alternating coverage.

**Reason/evidence:** prior return `review-4af247ba5b695e41:v0001` led to a reproduced seed-1/start-15 lesson where the whole-box rival fit four demos and failed only on a gapped query. Minimal current record: `counterexamples/review-8a556b3bdc6ddb5e/teaching_ambiguity_before.json`; regression: `tests/test_repair_schedule.py`.

## Executable semantics

`CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS` declare `fill_all_noncyan_bbox`. `SEMANTIC_WITNESSES` supplies a gapped internal-zero witness, `strict_canonical_like` tracks exact linked-profile support, and `lesson_identifiable` reports a rival that fits all demonstrations but changes the query.

Final evidence: 300/300 production lessons and 0/1,500 rotations ambiguous in the Racket census; a separate Python schedule probe checked 3,072 windows and 15,360 rotations with zero declared-rival failures. These are finite checks against declared rivals, not universal induction proofs.

## Input contract

`seed` and `sample_index` are literal integers; `sample_index` is nonnegative. Unknown overrides fail. All advertised overrides remain observable, and an explicit `zone_coverage` request takes precedence over the teaching schedule.

## Parametric proposal

`workspace/parametric/` contains an **unapproved** prototype choosing `target_colour` 3 or 4 once per episode. It preserves the canonical default and reasoning structure and is not connected to the production generator. Two retained episodes cover both values with no declared parameter ambiguity; four authored fixtures are not a production distribution.

## Open/inherited findings

1. Authority sync still reports exact-text divergence between canonical `program_solution` and selected `target_code`, although normalized text and execution agree; shared authority files were left unchanged.
2. The frozen baseline test uses a fixed `__file__.parents[...]` canonical path and blocks the official portable task-test stage before pytest. New focused tests pass through `workspace/run_focused_tests.py`, but the aggregate remains blocked until a maintainer migrates the frozen fixture to `reviewer_support` helpers.
## Current reviewer considerations

Source SHA-256: `9e8bb87bd4e4fdcac6af02d23c08e8bb676dac96ec4acbb9121de4ade733d3b1`.

# Decisions for `113d9bb402d3`

Final generator SHA-256: `9e8bb87bd4e4fdcac6af02d23c08e8bb676dac96ec4acbb9121de4ade733d3b1`
Canonical rule hash: `3b4315aa79fc`
Reference Racket changed: **no**

## D1 — Repair the lesson schedule, not the labels or rule

**Prior choice.** `zone_coverage` was sampled independently for each default draw. That was reasonable for single-grid diversity but supplied no lesson-level guarantee.

**Observed failure.** The retained production lesson at seed 1, easy, start sample 15 had coverage `complete, complete, complete, complete, gapped`. With the first four pairs as demonstrations, the plausible rival “fill every non-cyan bbox cell green” fit all demonstrations and changed the query. The exact differing cell and source binding are in `counterexamples/review-8a556b3bdc6ddb5e/teaching_ambiguity_before.json`.

**New choice.** Default coverage alternates deterministically by sample index with period 2: `gapped, complete`. The exported lesson assembly uses four demonstrations and one query from five consecutive accepted draws. Any query rotation leaves at least one gapped demonstration; in fact a five-pair window contains at least two gapped pairs.

**Why this approach.** It gives a transparent, testable guarantee without rejection loops, hidden retries, or changing valid individual grids. It is reproducible across workers and cheap to enumerate.

**Rejected alternatives.** Purely increase the random probability of gaps: this reduces but cannot remove the defect. Rejection-sample whole lessons until a witness appears: this hides variable work and complicates exact replay. Force every example to be gapped: this discards complete/canonical support and narrows the distribution unnecessarily.

**Failure modes and limits.** The period is visible and could interact with a downstream sampler that does not preserve consecutive indices. Therefore the generator declares the period, tests every query holdout, and reports the exact assembly policy. The guarantee is only against declared lesson competitors, not all conceivable rules.

## D2 — Keep four demonstrations and require arbitrary single-query holdout safety

**Choice.** `EXAMPLES_NEEDED=4`; lesson checks inspect five labeled pairs and hold out every position once where the downstream assembly permits it.

**Rationale.** Four demonstrations match the assigned solve/export policy and provide enough room for both complete canonical-like support and at least one gapped witness after any one pair becomes the query. The main semantic smoke check covered 12 lessons and 60 rotations; the full census covered 300 lessons and 1,500 rotations.

**Alternative rejected.** Treat the final pair as the only valid query and rely on order. That would be cheaper, but it would leave an avoidable positional shortcut and would not satisfy this task's supported rotation policy.

## D3 — Preserve canonical-profile frequency after reserving gapped slots

**Prior choice.** `_CANONICAL_PRIOR_P=0.32` applied to every draw.

**New choice.** Canonical profiles are complete rectangles, so they can only occur on complete schedule slots. The conditional prior is 0.64 on those slots, retaining about 0.32 pooled support while every other slot remains gapped.

**Evidence.** Final profile floor exact hits are easy 5/20, medium 10/20, hard 8/20, pooled 23/60 with no crashes. The larger semantic sample reports 192/600 exact canonical-like draws (32%).

**Risk.** Conditional probability and schedule parity are coupled. Focused tests and profile-floor checks bind both; changes to the schedule must revisit this calculation.

## D4 — Make scalar inputs strict

**Choice.** `seed` and `sample_index` must be literal Python integers; booleans, floats, strings, and `None` are rejected, and `sample_index` must be nonnegative.

**Rationale.** The baseline defect lint identified a public contract ambiguity. Silent coercion would make replay recipes and schedule residues unreliable.

**Alternative rejected.** `int(value)` coercion accepts booleans and lossy floats, creating multiple external recipes for the same draw.

## D5 — Turn the known shortcut into executable contract data

**Choice.** Add `rival_fill_all_noncyan_bbox` to all three public rival declarations, a gapped-box witness tied to that rival, `strict_canonical_like`, and `lesson_identifiable`.

**Rationale.** A prose note cannot prevent recurrence. The gate must execute the exact rival over actual demonstrations and query labels.

**Probe.** `workspace/verify_teaching_schedule.py` reads the generator's declarations rather than copying a rival-name list. It checked 3 bands × 16 seeds × 64 starts × 5 query positions = 15,360 rotations with no ambiguity.

**Limit.** The local probe uses `rule_mirror`; independent authority comes from the Racket census. Both remain finite and task-specific.

## D6 — Prototype one meaningful rule parameter, separate from production

**Parameter chosen.** `target_colour ∈ {3,4}`, chosen exactly once per episode. The canonical default remains 3; 4 is produced by replacing exactly one guarded recoloring site in the hash-pinned canonical Racket text.

**Why meaningful.** It changes the transformation's output relation for every selected inside-blue cell rather than cosmetically changing inputs. Object roles, cyan bounding-box relation, selective recoloring, and all input constraints remain unchanged.

**Why only two values.** A two-value prototype is enough to exercise episode-level selection and identifiability without introducing a broad color-role policy or conflicting with fixed canonical colors.

**Alternatives rejected.** Parameterizing cyan as another color would change the rule's semantic marker and require a broader role-permutation audit. Parameterizing geometry or gap policy changes the input distribution rather than the rule. Adding the parameter to production now would imply API/training approval not granted by this assignment.

**Evidence.** Two seeds cover both settings; each has 3 demos + 1 query; the other parameter value is refuted by all demos; 0 declared ambiguities; exact hashes and Racket outputs are in `checks/parametric/episodes/report.json`.

## D7 — Do not change Racket authority to clear an unrelated exact-text gate

**Choice.** Leave canonical `program_solution`, selected `target_code`, and archival `raw_code` unchanged.

**Reason.** All three execute correctly on all canonical pairs, and canonical/selected normalized hashes agree. The remaining gate failure is exact textual synchronization in shared authority data, outside the task-local generator repair. Changing it would obscure the fact that the lesson defect required no rule change.

**Evidence.** `checks/after/checks/113d9bb402d3_after_authority_sync.json` reports execution parity `PASS` and suggests a separate selected-only formatting synchronization.

## D8 — Preserve the frozen test blocker and add a replayable focused runner

**Choice.** Do not edit the issued `test_generator_113d9bb402d3.py`. Add `workspace/run_focused_tests.py`, which constructs a clean mini-runtime and runs only the two reviewer-added test files while recording all source hashes.

**Reason.** The official task-test stage correctly blocks before pytest on the frozen fixture's fixed-depth canonical path. Masking or deleting that failure would be misleading, but the new repair and prototype tests still need independently replayable evidence.

**Evidence.** Official result: `checks/task-tests/result.json` (`preflight_failed`, exit 2). Focused result: `checks/final-focused/result.json` (10 passed, exit 0).

## D9 — Evidence retention and compression

The 100-per-band Racket census produced a 26,325,365-byte JSON report, above the return's expanded evidence budget by itself. It was losslessly compressed to `checks/lesson-census.json.gz`; `checks/lesson-census.compression.json` records original/compressed size and SHA-256 plus restoration instructions, and `checks/lesson-census.summary.json` retains the acceptance-critical counts. The original uncompressed file was removed only after a byte-for-byte gzip round-trip check.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-4af247ba5b695e41:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `b5e965f505173cf9843556ceebe86a5c95310ea63a0dc594080177e8ff175a63`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicitly resolve old b5e965f5 fill-all-noncyan-bbox teachingfinding againstcurrent9e8bb87b gapped/complete period2 schedule:15360reportedrotations and30actualRacket schedule rotationsrefuterival. No sourceeditthisintake. Newcurrent-source frozenfixture issue remains separatelyunresolved;oldteachingclosuredoesnotclaimaggregatepass.

### Assessment or prior finding

## 113d9bb402d3

**Reproduced teaching defect — “fill the whole cyan bounding box” survives four demonstrations and changes the query.**

Current generator SHA-256: `b5e965f505173cf9843556ceebe86a5c95310ea63a0dc594080177e8ff175a63`. Current canonical rule hash: `3b4315aa79fc`; the supported Racket `apply` receipt agrees with the Python mirror on all five materialized pairs.

The intended rule recolors only blue cells inside the cyan bounding box. The plausible rival instead recolors every non-cyan cell in that box, including background zeros. It is identical on `zone_coverage="complete"` examples and differs on `zone_coverage="gapped"` examples.

The supported production generation CLI emitted an exact ambiguous lesson with no rejections:

- difficulty `easy`, seed `1`, requested start sample index `15`;
- accepted sample indices `15,16,17,18,19`;
- four demonstrations all had `zone_coverage="complete"`;
- the query had `zone_coverage="gapped"`;
- the rival matched all four Racket-labelled demonstrations and changed the query answer.

Evidence: `checks/audit/113d9bb402d3/lesson.jsonl`, `inputs.json`, `racket.json`, and `probe.json`. Every input passed the target validator. This is a concrete production-materialized lesson defect, not merely a possible combination; broader frequency was not measured.

No files for this audit target were changed. Recommended repair: declare the whole-box-fill rival and require a gapped witness in the demonstrations whenever a gapped query is possible, preferably through a deterministic lesson schedule rather than rejection sampling.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-4af247ba5b695e41-v0001/audit_assets.json), manifest SHA-256 `e89ce08a65ab3c6afd9525ec54e29eb213403153265f53e4dc5ded165240f3d3`.
<!-- arcpuzzles-current-audit-assessment:end -->
