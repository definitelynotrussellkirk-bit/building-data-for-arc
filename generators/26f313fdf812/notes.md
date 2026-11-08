# Working notes: 26f313fdf812

## Current rule and authority

The selected authority orders nonzero same-color 4-connected components by bounding-box top-left `(min_row, min_col)`, compares their **cell counts**, and emits an `N×N` matrix with `1` for equal, `2` for row-object larger, and `3` for row-object smaller. `RULE_HASH = "80930b679862"` remains pinned. No Racket authority or canonical data changed in this review.

Current generator version: `3.1.0`. Final generator SHA-256: `a7ae251a40ef234a542abb1167b32c3507d99ff3f7c7dfb10a1a50e7c95c57e6`.

## Repaired accepted-domain coverage gap

The retained audit from `review-43bfa46e57f55f67:v0001` was used as the lead. On baseline SHA-256 `7860fb33fe86183a8f0898e568c0efdf569cbcdea4ca5dafd455699001429d4e`, row-major component encounter order agreed with bounding-box top-left order on all 5 canonical pairs and 600/600 sampled inputs. The retained lawful counterexample is `counterexamples/review-43bfa46e57f55f67-v0001/retained/checks/audit-26f313fdf812-counterexample.json`.

Prior choice: every object occupied a separated 3×3 envelope. That made an object's first row-major cell coincide with the ordering implied by its bounding box, so the generator could not teach the distinction.

New choice: rank profiles place a 7-cell leftward hook and a 2-cell horizontal object on the same top row. The hook's bounding box starts farther left, but its first occupied cell is farther right. The intended bbox order and the plausible scan-encounter rival therefore produce different matrices. The generator now declares that rival, its witness, and a lesson-level requirement.

## Lesson schedule decision

Every lesson has four demonstrations and one query. The easy cycle now has two `n=3` and two `n=4` profiles, with one tie and one bbox-versus-scan rank witness at each object count. The medium cycle pairs tie/rank profiles at `n=3/4/5`; all three rank slots are ordering witnesses. This makes every single-pair query rotation retain dynamic-size, tie, same-row, and bbox-versus-scan evidence.

An intermediate generator (`aae889c163ae78ba3ec24645ddc4d81fb664b943efbab3c2999914edb543d5d9`) passed the ordinary 12-stage battery and 12/12 production lessons, but the diagnostic found 8/60 ambiguous query rotations. Easy rotations could hold out the sole `n=4` example; medium rotations could hold out the sole scan-order witness in a five-pair window. The final schedule removes both single points of evidence.

## Final measured evidence

- Full after battery with required rotations: 12/12 stages green. Semantic gate: 600/600 strict draws, 12/12 four-demo production lessons identifiable, all 8 declared rival claims held, and 0/60 ambiguous rotations. Evidence: `checks/after-final/checks/26f313fdf812_after_battery_summary.json` and `checks/after-final/checks/26f313fdf812_after_semantic_gate.json`.
- Portable selected-task tests: 11/11 passed. Evidence: `checks/task-tests-final/result.json`.
- Larger production census: 300/300 lessons materialized and identifiable, 1,500/1,500 query rotations identifiable, 1,500 unique pair inputs, no hook/scoring/materialization errors. Evidence: `checks/lesson-census-final.json`.
- Exhaustive declared-cycle probe at one deterministic seed family: 14/14 production windows and all 70/70 rotations passed. It also sampled 64 inputs from each of four ordering-witness profiles (256 unique inputs), with zero validator failures and zero scan-rival agreements. Tool: `tests/probe_ordering_curriculum.py`; evidence: `checks/order-scan-probe-final.json`.

## Assumptions and limits

- The documented normal domain still requires each nonzero color to form one connected object. Grouping disconnected same-color components is therefore an explicit out-of-domain question, not repaired here.
- The finite competitor set does not prove unique induction against every possible program. It covers the declared shortcuts plus the newly reproduced scan-encounter rival.
- The cyclic probe exhausts schedule starts and query positions for the declared cycles at its fixed seed family; the 300-lesson census broadens seeds but is still finite.
- The repository-wide `pytest -q` collection is blocked by a packet-level missing file, `shared/tools/arc_review_guard.py`, in `tests/test_review_resource_restore.py`. This is outside the selected-task edit boundary; task-local portable tests and the full generator battery are green.

## Current audit resolution

Exact v3.1.0 repair adds interleaved bbox-versus-first-cell witness, scan-order competitor and rotation-safe lesson schedules. Reviewer reports 11/11 task tests, 12/12 required-rotation battery, 300 lessons/1500 rotations and cycle probe. Closes only the bbox-order support finding; repeated-color domain question remains separate.

Closure is reviewer-reported on the exact repaired source. Detailed current assessment: `evidence/current-audit-assessment.json`.
## Current reviewer considerations

Source SHA-256: `a7ae251a40ef234a542abb1167b32c3507d99ff3f7c7dfb10a1a50e7c95c57e6`.

# Decisions for 26f313fdf812

## D1 — Treat the retained scan-order finding as an accepted-domain defect

- **Prior state:** Baseline version `3.0.0`, SHA-256 `7860fb33fe86183a8f0898e568c0efdf569cbcdea4ca5dafd455699001429d4e`, used separated compact envelopes. The original rationale for requiring those exact envelopes is not recorded; they appear intended to make object placement safe and ordering obvious.
- **Evidence:** Retained return `review-43bfa46e57f55f67:v0001` supplies a hand-constructed grid that passes both `self_check` and `strict_canonical_like` but makes bbox-top-left order disagree with row-major first-cell order. The rival fit all 5 canonical pairs and 600/600 baseline samples.
- **Decision:** Repair the sampler and semantic contract rather than classifying the issue as out of domain.
- **Rejected alternative:** Merely sample more seeds from the existing envelope construction. That cannot expose the distinction because it preserves the structural cause.
- **Failure mode considered:** A new shape might touch or merge another object, leave the ARC bounds, or change canonical object extraction. Focused tests require both validators to remain clean.

## D2 — Use a small deterministic interleaving witness

- **Choice:** In rank profiles, place a 7-cell leftward hook first by bbox origin and a 2-cell horizontal object second by bbox origin, while reversing their row-major first-cell order.
- **Rationale:** This is the smallest stable construction found that makes the two order conventions observably different without changing the task domain. Unequal areas guarantee that reversing the components changes the output matrix.
- **Alternatives considered:**
  1. Randomly search arbitrary connected shapes until an ordering disagreement occurs. Rejected because it complicates reproducibility, bounded runtime, and profile guarantees.
  2. Move one compact object so its first cell differs from its bbox origin. A compact 3×3-envelope object generally still exposes the leftmost top cell, so this did not address the root cause.
  3. Add only the retained hand-built counterexample as a special profile. Rejected in favor of a general witness branch present across `n=3`, `n=4`, and `n=5` profiles.
- **Probe:** `tests/probe_ordering_curriculum.py` sampled 64 inputs for each of four witness profiles; all 256 were unique, validator-clean, and disagreed with the scan rival.
- **Known limitation:** The leading areas and shape pair are fixed at `(7,2)`. This guarantees the witness but provides less geometry diversity than a family of interleaving shapes.

## D3 — Declare the plausible rival and require it at lesson level

- **Choice:** Add `scan_order_not_bbox_top_left` to `SEMANTIC_RIVALS` and `LESSON_COMPETITORS`; add `bbox_top_left_not_scan_order` to `SEMANTIC_WITNESSES`; bind them in `WITNESS_RIVALS`; require at least one such demonstration in `lesson_identifiable`.
- **Rationale:** A distribution change alone can regress silently. Executable rival/witness declarations make the intended distinction measurable in the shared semantic gate and larger census.
- **Rejected alternative:** Add only a unit test for one seed. That would catch deletion of the exact witness but not prove complete lessons still refute the shortcut.
- **Failure mode considered:** A witness can fire on a pair while the complete lesson still leaves the rival alive. The lesson-level requirement plus competitor survivor check covers this.

## D4 — Preserve the Racket authority

- **Choice:** Keep `RULE_HASH="80930b679862"`; do not edit canonical examples or authority files.
- **Rationale:** The retained counterexample confirms that the reference already expresses the intended bbox-top-left semantics. The defect was coverage, not labels or rule implementation.
- **Verification:** Rule smoke, Racket lint, and authority sync are green; final authority-set SHA-256 is `279924e76ac3682f55cbe4eb6c500092acfe16c78542eec02c19989579e2010c`.

## D5 — Upgrade the schedule after the first repair’s rotation diagnostic

- **Initial repaired schedule:** It passed all 12 ordered smoke lessons, but the diagnostic found 8/60 ambiguous held-out rotations on intermediate SHA-256 `aae889c163ae78ba3ec24645ddc4d81fb664b943efbab3c2999914edb543d5d9`.
- **Root causes:**
  - Easy: three `n=3` slots and one `n=4` slot meant holding out the unique `n=4` pair left no evidence for dynamic output size.
  - Medium: only two ordering-witness slots in a six-profile cycle meant some five-pair windows had one witness; holding it out left the scan-order rival alive.
- **Final choice:**
  - Easy: two `n=3` and two `n=4` profiles, each count represented by one tie and one rank/ordering witness.
  - Medium: tie/rank pairs at `n=3/4/5`; mark `c10x12_n3_rank` as an ordering witness so every five-pair window contains at least two.
- **Alternatives considered:**
  1. Declare fixed-last-query ordering and leave rotations unsupported. Rejected because the strengthened schedule was inexpensive and safer for downstream shuffling.
  2. Increase `EXAMPLES_NEEDED`. Rejected because four demonstrations already suffice when evidence is balanced.
  3. Duplicate a single profile. Rejected because pairing tie/rank evidence at each object count is more systematic and retains profile diversity.
- **Verification:** Required-rotation semantic gate reports 0/60 ambiguous; 300-lesson census reports 0/1,500 ambiguous rotations; cyclic probe reports 70/70 rotations passing.

## D6 — Keep disconnected same-color components out of normal scope

- **Prior finding:** `review-27c79f069ba07405:v0001` retained a color-grouping versus connected-component domain question.
- **Decision:** Do not broaden this repair. The current invariant explicitly requires each nonzero color to form one connected object, and the retained witness is rejected by `self_check`.
- **Rationale:** Expanding repeated-color support would be a separate domain/architecture decision and could affect object identity, palette assignment, and canonical compatibility.
- **Limit:** Training does not distinguish component identity from color grouping outside the declared domain.

## D7 — Build a reusable source-bound probe

- **Choice:** Add `tests/probe_ordering_curriculum.py` rather than keep a one-off shell snippet.
- **Capabilities:** Independently extracts components in scan order, checks the rival against generated outputs, records a concrete first witness, samples every ordering profile, checks all production cycle starts, and checks every query rotation.
- **Rationale:** Future agents can re-run it after schedule, shape, or semantic-contract changes without reconstructing the audit.
- **Limit:** The cycle section uses a fixed deterministic seed family; the larger random census provides broader but still finite seed coverage.

## D8 — Report the repository-wide pytest collection blocker without crossing scope

- **Observed failure:** Root `pytest -q` stops in `tests/test_review_resource_restore.py` because `shared/tools/arc_review_guard.py` is absent from this review packet.
- **Decision:** Preserve the exact log and report it; do not add or modify shared files because the assignment permits edits only under the selected task.
- **Compensating verification:** Portable task tests pass 11/11, and the final authority-bound battery passes all 12 stages.
