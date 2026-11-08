# Working notes: 9fe97c2dd8a4

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-03 review `review-3a689738d8a967ca`

Used retained return `external-local-random:4ab57ced1620` as a lead, then replayed the pinned baseline. The executable rival “include color-5 bars in the duplicate census” survived 39/100 easy, 28/100 medium, and 42/100 hard four-demo windows. Version 2.1.0 now exports the rival, constructs answer-changing gray cases (including modulo-10 collision filtering), and makes every cyclic four-demo window refute it. Final source SHA is `33cef6801dbee98be442d197810d1a3e604c046bfdd1b544a29f0da18d62e381`; the 12-stage after battery is all green and the 300-lesson probe has zero survivors.

A first repaired source failed the distribution gate because palette cardinality 6 was unreachable; a test-first patch gives the four-bar duplicate phase four distinct non-gray colors. Selected Racket `target_code` was formatting-synchronized to canonical while archival `raw_code` and rule hash `c7281f787d6e` remain unchanged.
## Current reviewer considerations

Source SHA-256: `fd94fa93f385478fcf37f0ce83f899675c757b0b2d1e5d1cbf36884fafb1b5a5`.

# Decisions for review-c68d90ff749e6880

## D1. Use retained review-36ef73706f62e68c-v0001 only as a lead

**Input choice and prior rationale.** The retained audit identified a row-position-conditioned rival on baseline SHA `33cef6801dbee98be442d197810d1a3e604c046bfdd1b544a29f0da18d62e381`: apply duplicate adjustment only when bars start on row 1. Its census reported 91 answer-changing accepted defects among 1,500 lesson windows.

**Alternatives.** Trust the prior count without replay, ignore it, or reopen every historical return.

**Probe and decision.** I reproduced the rival on the pinned baseline, then wrote an executable competitor and exhaustive task-local cyclic-window regression. Historical files remain evidence of the old source, not measurements of the repair.

**Limitation.** The rival set is finite and human-authored; passing it does not prove unique induction against every possible program.

## D2. Reject scalar coercion at the public generator boundary

**Original choice.** Version 2.1.0 delegated integer values to permissive draw helpers and coerced values with `int(...)`; the before defect linter found 123 strict-scalar cases, including `bar_count=6.75` accepted as exact 6, bools accepted as integers, string/float seed and sample index coercion, and negative sample indices.

**Alternatives.** Keep coercion for convenience, patch only `bar_count`, or rely on downstream helpers.

**Decision.** Require exact Python `int` (not `bool`) for seed, sample index, and integer overrides; require a declared difficulty; reject negative sample indices; use `draw_int_strict` for exact controls.

**Probe.** `tests/test_review_repairs.py` was red on 30 scalar cases before the change and is green afterward. The final full defect-lint result is recorded under `checks/after-pass/`.

**Failure mode avoided.** Metadata can no longer claim an exact control value while the generated sample silently uses a truncated one.

## D3. Declare and execute the row-start-gated duplicate rival

**Original rationale.** Unknown. Canonical examples happened to correlate duplicate adjustment with bars beginning on row 1, and the baseline lesson contract knew only the color-5 census rival.

**Alternatives.** Treat row placement as harmless decoration, add a prose warning only, or change the canonical rule.

**Decision.** Add `duplicate_adjustment_only_when_bars_start_row_1` to `LESSON_COMPETITORS`; keep the canonical Racket rule unchanged.

**Probe.** `counterexamples/review-c68d90ff749e6880-row-start.json` is a final-source row-2 duplicate scene where Racket and the rival differ in two output cells. The focused regression checks every five-slot cyclic start, three bands, and seeds 0–11.

**Failure mode avoided.** A four-demo lesson can no longer teach that row placement gates duplicate semantics.

## D4. Make row-2 duplicate witnesses causal, not merely structural

**Choice.** Reserve phases 1 and 3 for row-2 duplicate scenes, disable canonical-profile substitution in those slots, and choose at least one non-anchor length whose duplicate-adjusted digit differs from its ordinary digit after modulo-10 squaring.

**Alternatives.** Move every bar to row 1, rely on random row-2 occurrences, or accept a duplicate scene even when modulo-10 collisions make the rival observationally identical.

**Probe.** The row-start regression checks that every four-demo cyclic window contains a demonstration on which the rival disagrees, then checks `lesson_identifiable(...) == []` for the complete lesson.

**Limitations.** The fixed five-slot schedule deliberately structures branch coverage; it is not a claim of uniform sampling over all lawful scenes.

## D5. Make exact canonical profile support deterministic

**Failure discovered.** The first repaired after battery (`checks/after-final/`) passed 11/12 stages but had zero exact hard-band profile hits. Bumping `VERSION` reseeded the former probabilistic 30% canonical prior, exposing that profile support depended on luck.

**Alternatives.** Revert the version, tune the prior until the current seeds happen to pass, add a profile-floor opt-out, or force all slots to canonical examples.

**Decision.** Phase 0 always selects one of the ordinary exact canonical profiles; phases 2 and 4 retain a 30% prior, while witness phases 1 and 3 remain generated row-2 scenes. Version is `2.2.1`.

**Probe.** A test reproducing the gate’s pinned seeds failed with `('hard', 0)` before the change. The exact stage then passed with easy 7/20, medium 10/20, hard 5/20, pooled exact 22/60 and envelope 37/60 (`checks/profile-floor-final/checks/9fe97c2dd8a4_after_profile_floor.json`).

**Failure mode avoided.** Future version changes cannot erase all canonical support merely by shifting RNG draws.

## D6. Preserve the canonical authority and propose only one bounded parameter

**Decision.** The production rule remains encoding power 2 and rule hash `c7281f787d6e`. The task-local prototype adds episode-fixed `encoding_power ∈ {1,2}`; power 2 materializes the exact canonical Racket text and power 1 writes `abs(base) mod 10`.

**Alternatives.** Modify production generation, vary a cosmetic input property, add several interacting parameters, or omit Racket execution.

**Probe.** `workspace/parametric/prototype.py` creates two complete episodes, executes selected and rival labels in Racket, rejection-samples only inputs where settings differ, and emits public files without hidden parameters or query labels. Final evidence is under `checks/parametric/final-v2/`; focused tests pass 2/2.

**Limitations.** This is a proposed prototype, not selected production behavior or training approval. It compares only two declared settings and does not prove identifiability against undeclared rules.

## D7. Keep the frozen task fixture unchanged

**Failure.** The official portable task-test stage stops in preflight because inherited `test_generator_9fe97c2dd8a4.py` resolves canonical data through a fixed parent depth. Evidence: `checks/task-tests/result.json`.

**Alternatives.** Edit the frozen fixture, omit the official task-test run, or misreport direct focused tests as an aggregate pass.

**Decision.** Leave the frozen file unchanged, retain the blocker, and report completion state `blocked`. New portable tests are run directly and later replayed in a fresh extraction.

**Limitation.** The aggregate task-test stage has no passing count even though the new files pass, because preflight aborts before pytest.

## D8. Keep audit targets findings-only

The assigned audits `c8f4bbd87f63` and `69fcc82f9e3c` were inspected and reproduced at their assigned source hashes. I changed neither target. Exact Racket outputs and a portable reproduction script are under `checks/audit/`; conclusions are in `AUDIT.md`.

## D9. Stop at source-bound finite evidence

The repair tests declared rivals, cyclic starts, pinned canonical-profile seeds, strict scalars, and Racket authority. They do not prove universal identifiability, uniform distribution, or the suitability of the proposed parameter for production. Those limits remain explicit rather than being promoted to approval claims.
