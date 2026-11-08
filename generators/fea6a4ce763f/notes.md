# Working notes: `fea6a4ce763f`

## Current rule and authority

Find all nonzero monochromatic 4-connected components, choose the unique largest by cell count, and return its tight bounding-box crop while preserving background holes. Generator version `3.1.0`; source SHA-256 `782c5f1cfb527a4f3e95a1c33c8c08cd0fe4438ee44b67597386ac81b0e7ede1`; canonical rule hash `5f27f31fdbe8`. Racket authority and canonical JSONL were not changed.

## Current distribution

- Five exact canonical `(height, width, used-color-count)` profiles cycle by sample index.
- Public override surface is exactly `scene_profile`; invalid/unknown axes and invalid request scalars reject.
- Semantic phases still alternate `split_distractor` on even indices and `split_target` on odd indices; combined profile/phase period is ten.
- Every tenth `split_distractor` is a canonical-structure bridge with no singleton markers, closing the measured canonical/generated object-count gap.
- Ordinary `split_distractor` scenes refute global color aggregation; `split_target` scenes split both target and globally dominant distractor and refute five declared canonical-fitting rivals.
- Difficulty changes keyed palette/layout randomness without changing rule, profile, or witness guarantees.

## Current decisions

1. Preserve `(rule! extract-largest)` and repair only generator contracts/curriculum.
2. Centralize exact request validation for seed, non-negative index, and `None|easy|medium|hard`.
3. Preserve the public two-phase API; embed structural bridges at period boundary rather than add a third phase.
4. Add `densest_component_min4` because it fits all five canonical pairs; require generated disagreement.
5. Keep the inherited fixture byte-identical and add assignment tests separately.
6. Keep the `four|eight` connectivity extension isolated under `workspace/parametric/`; it is proposed, not production authority.

## Evidence

- Before: `checks/before-current/checks/fea6a4ce763f_before_battery_summary.json` — 11/12; only defect lint failed.
- Final: `checks/after-enumerated/checks/fea6a4ce763f_after_battery_summary.json` — 12/12 green with all ten schedule starts enumerated and rotations required.
- Portable task tests: `checks/task-tests-final/result.json` — 68/68.
- Fresh return replay: `checks/fresh-replay/summary.json` — full original extraction, 13 patched paths hash-checked, replayed task tests 68/68.
- Lesson census: `checks/lesson-census.summary.json` — 300 lessons, 1,500 pairs, zero production/rotation ambiguity, 1,494 unique inputs.
- Parametric evidence: `checks/parametric/connectivity-v1/summary.json` — both settings, 5/5 canonical default, 23 Racket receipts.
- Static shortcut witness: `counterexamples/most_frequent_color_split_distractor.json`.

## Prior lead

The same-rule review at `repo/generators/db89dc496d45/` was consulted only for its aggregate-color warning and probe pattern. Its measurements are not used here.

## Known limits and open findings

The emitted morphology remains narrow: five canonical profiles, corner/gutter construction, sparse 6/7-cell targets, and a finite named-rival set. Passing the census is not a universal identifiability proof. The parametric prototype has two settings and two retained episodes only; it has no approval or training claim. No selected-task gate remains failing.
## Current reviewer considerations

Source SHA-256: `782c5f1cfb527a4f3e95a1c33c8c08cd0fe4438ee44b67597386ac81b0e7ede1`.

# Decisions — `fea6a4ce763f` review `review-f77da5fd4f646b23`

## D1 — Treat v3.0.1 as the actual baseline

**Prior choice:** the packet-selected baseline already exposed one exact `scene_profile` axis, alternated `split_distractor` and `split_target`, declared four canonical-fitting color rivals, and pinned rule hash `5f27f31fdbe8`. Older v2.2.3 history remains useful context but is not the before measurement for this assignment.

**Decision:** repair only defects reproduced against baseline SHA `ffa7baa5b79591d30172bc4877d78d2429b2d04c5f7c241659807184ef3df289`.

**Reason:** the before battery showed one failing stage, not a need to redesign the entire generator. Replaying old changes would obscure the actual delta and risk breaking a mostly green source.

## D2 — Preserve the Racket authority

**Decision:** keep `(rule! extract-largest)`, canonical JSONL, and rule hash `5f27f31fdbe8` unchanged.

**Reason:** rule smoke, canonical acceptance, Racket lint, and authority sync were green before repair. Both reproduced defects were generator-contract defects, not wrong reference semantics.

**Rejected alternatives:** change the rule to aggregate by color, add a tie-breaker, or switch to 8-connectivity. Each would contradict the canonical connected-component abstraction. The 8-connectivity idea is retained only as a separate parametric prototype.

## D3 — Validate request scalars at one boundary

**Prior choice:** `generate` checked that seed and sample index were `int`; helper functions checked only sample-index type; unknown/invalid difficulties fell through to a mixed keyed-randomness branch.

**Decision:** `_validate_request` requires exact integers (not booleans), a non-negative sample index, and difficulty `None`, `easy`, `medium`, or `hard`. `generate`, `schedule_profile`, and `semantic_phase` all call it.

**Reason:** defect lint found 18 accepted-invalid-scalar cases. Central validation prevents helper/API divergence while keeping valid deterministic recipes unchanged.

**Failure modes tested:** negative index, boolean/float/string difficulty, boolean seed/index, and valid `None`/three bands.

## D4 — Close the canonical coarse-structure gap without changing the public phase API

**Prior choice:** every generated p4 scene had singleton palette markers; no draw matched the canonical object-count/marker-count support. A first experiment introduced an explicit third `canonical_bridge` phase in a five-step schedule.

**Decision:** retain the public two-phase alternation and ten-step combined schedule. At indices divisible by ten, realize `split_distractor` as a canonical-structure bridge: target plus two compact non-singleton distractors for p4, with one extra domino for p5.

**Reason:** the bridge removes the measured structural mismatch while preserving `semantic_phase(index)` behavior, profile cycling, and contiguous four-demo lesson assumptions.

**Rejected alternative:** keep the explicit three-phase experiment. It altered the public phase vocabulary and five-step schedule, and its bridge did not by itself refute the density shortcut. The experiment is retained in `workspace/generator-v3.1.0-bridge-experiment.py` as a failed iteration.

## D5 — Add the strongest newly exposed canonical-fitting rival

**Observation:** `densest_component_min4`—choose the densest component with at least four cells—fits all five canonical labelled pairs. The inherited sparse target versus compact distractor curriculum could let it survive.

**Decision:** declare it beside the four existing color rivals. Require bridge draws to disagree with it, and require `split_target` to disagree with all five rivals.

**Reason:** this directly tests whether the structural bridge accidentally teaches “pick the compact object” rather than “pick the largest component.” The final semantic gate records canonical fit and generated refutation.

**Limit:** a finite rival set is not complete; future agents should add a rival only with canonical-fit validation and a concrete generated disagreement.

## D6 — Strengthen `split_target` rather than add ad hoc labels

**Prior choice:** the target color was globally most frequent, with one detached target fragment; the other split color used two triominoes.

**Decision:** use a seven-cell target, two five-cell pieces of the globally dominant distractor, and a detached target fragment. The intended largest component stays unique, while both relevant colors are split.

**Reason:** one family now refutes all aggregate-color and conditional color-ranking rivals as well as the density rival. This is easier to audit than mapping different weak properties to several micro-phases.

**Failure modes:** target tie, connected split pieces, out-of-bounds placement on the smallest profile, omitted palette color, and crop without an internal zero are covered by tests/self-check/battery.

## D7 — Keep the production lesson order and enumerate the declared period

**Decision:** continue four demonstrations plus one query in production order. Keep `LESSON_SCHEDULE_PERIOD = 10`; for final acceptance, enumerate all ten fixed-seed starts and require every query rotation identifiable.

**Reason:** the standard after command correctly warned that sampled smoke checks do not prove fixed-seed period coverage. Rather than remove the declaration or suppress the warning, the stronger run supplied the missing proof.

**Evidence:** standard run `checks/after/` is retained as an 11/12 failure; `checks/after-enumerated/` is 12/12 green; the larger census has 0/1,500 ambiguous rotations.

## D8 — Preserve the inherited frozen fixture

**Decision:** leave `tests/test_generator_fea6a4ce763f.py` byte-identical (SHA-256 `1156d19cb40c940033a0a66f2283641c1cafbe3b28cbf294ed33494aeb664872`). Put all assignment-specific tests in `test_review_f77da5fd4f646b23.py` and parametric tests in `test_parametric_connectivity.py`.

**Reason:** the packet explicitly declares the inherited root fixture frozen. Separate tests also make the new contract and prototype removable/auditable without rewriting history.

## D9 — Retain a source-bound static shortcut witness

**Decision:** refresh `counterexamples/most_frequent_color_split_distractor.json` using final source seed `210000`, index `2`, easy, profile `canonical_7x9_p4`, and a supported Racket apply receipt.

**Reason:** it gives future agents a small exact regression for the strongest simple aggregate-color shortcut, independent of a large census. The regression verifies final generator hash, self-check, witness firing, rival disagreement, and Racket/Python equality.

## D10 — Prototype connectivity as the one suitable rule parameter

**Alternatives considered:** component connectivity, selection metric, tie handling, background color, and crop padding. Connectivity was selected because it changes one crisp relation while preserving the original reasoning chain. Selection metric would collapse into the already-tested shortcuts; tie handling has no canonical evidence; background/padding change object roles or output grammar rather than a small rule parameter.

**Decision:** provide `connectivity = four|eight`, defaulting to the exact canonical program. Choose it once per episode. Use diagonal contact so every one of three demonstrations distinguishes the hidden setting, then retain one query.

**Evidence:** `workspace/parametric/`, `checks/parametric/connectivity-v1/summary.json`, two Racket program hashes (`5f27f31…` and `88f5439f…`), 23 execution receipts, and 9 passing tests.

**Status:** proposed prototype only. The intentionally narrow input grammar and two episodes are insufficient for production or training approval.

## D11 — Keep prior leads separate from measurements

The same-rule notes at `repo/generators/db89dc496d45/` were used only as a lead for aggregate-color confounding and probe structure. No result from that source is counted as evidence for this generator. All reported counts are from current source-bound checks.

## D12 — Stop after source-bound green evidence

The selected task has no remaining failing gate. The standard non-enumerated warning is superseded—not erased—by the stronger complete schedule run. Remaining uncertainty is conceptual completeness against undeclared rules and natural-input breadth, both documented rather than “fixed” through ungrounded random complexity.
