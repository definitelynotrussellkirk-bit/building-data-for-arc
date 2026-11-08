# Current notes: 72416068b0cf

## Intended rule

Row 0 encodes `(shape_code, step1, step2)`. In the body, choose the unique monochrome object whose normalized binary crop exactly equals the selected orientation-specific template, preserve its color, crop it, and apply the two D4 transforms in header order. The canonical Racket rule is unchanged and pinned by `RULE_HASH=7dc6818bbe6b`.

## Generator and lesson assumptions

- Lawful calls use exact integer `seed` and non-negative exact integer `sample_index` values; difficulty is `None|easy|medium|hard` and only declared integer overrides are accepted.
- Four consecutive generated demonstrations are an ordered curriculum. They cover shape codes 1–4 and transform codes 1–7; the following pair is the query.
- Seed-derived offsets permute code identities while preserving four-window coverage. Position scheduling includes target-first and target-not-first examples. Two/three distractors include equal-size and larger alternatives.
- Canonical-profile anchors occur every fifth sample; other samples retain banded dimension and distractor diversity.

## Review decisions and reversals

- **Prior:** partial rivals were listed in `CANONICAL_SHORTCUTS`. **Now:** that mapping is empty because every retained rival fails at least one labeled canonical pair; the hypotheses remain lesson/semantic rivals where appropriate.
- **Prior:** shape-code presence checks were semantic witnesses without rival claims. **Now:** all retained witnesses are executable disagreements with named rivals; full shape/code coverage is enforced by `lesson_identifiable`.
- Reverse transform order is explicitly scored as a lesson competitor and witnessed when noncommutativity changes the answer.
- Invalid identity scalars are rejected before shared context creation.

## Evidence and limits

Final generator SHA-256 is `2e09fb8f2931a6de25636484487c4bf08ccc8116428a7298ab21951042e3cfd1`. The final battery has 12/12 green stages and selected tests pass 27/27. A 300-lesson census has 0/300 ambiguous ordered production lessons and 1,500 unique inputs, but arbitrary query rotation has 135/1,500 ambiguous holdouts, usually because the held-out pair removes complete code coverage and reverse order survives. Downstream assembly must keep the ordered fifth-query policy or rerun identifiability/resample rotated lessons.

The declared rival set is finite; passing it does not prove universal identifiability. The random census does not exhaust all seeds. No training approval is implied.

## Proposed parameter

`workspace/parametric/` contains a non-production prototype for episode-level `composition_order = forward|reverse`. Forward is canonical. Each retained example episode has four Racket-labeled demonstrations and one query that distinguish the chosen setting from its rival. The prototype does not change canonical execution or approval status.
## Current reviewer considerations

Source SHA-256: `2e09fb8f2931a6de25636484487c4bf08ccc8116428a7298ab21951042e3cfd1`.

# Decisions for `72416068b0cf`

## D1 — Keep the canonical Racket rule unchanged

- **Input choice:** Preserve the selected authority program and declared `RULE_HASH=7dc6818bbe6b`.
- **Rationale:** Canonical smoke and authority checks already agreed; the reproduced defects were generator-contract and semantic-metadata defects, not output-law defects.
- **Alternatives considered:** Rewrite transform composition or shape selection in Racket; rejected because that would add authority risk without addressing the failures.
- **Probe/evidence:** Before battery failed only `defect_lint` and `semantic_gate`; final `rule_smoke`, `racket_lint`, and `authority_sync` are green in `checks/after/result.json`.
- **Limitation:** Finite checks do not prove the Racket program for every possible grid, only the declared lawful grammar and retained canonical/generated samples.

## D2 — Enforce exact call identity

- **Prior choice:** The generator delegated seed/sample handling to shared context and accepted bool, float, string, and negative identities.
- **New choice:** Require `type(seed) is int`, `type(sample_index) is int`, and `sample_index >= 0` before constructing context.
- **Rationale:** Reproducibility depends on one unambiguous call identity; Python bools are integers semantically but should not alias seeds here.
- **Alternatives:** Coerce values with `int(...)` or permit bools; rejected because both silently merge distinct caller mistakes.
- **Probe/evidence:** Red regressions in `checks/tdd-red/result.json`; final tests in `generators/72416068b0cf/tests/test_review_hardening.py`; final defect lint green.
- **Failure mode:** This is intentionally stricter for malformed callers, but does not affect lawful integer calls.

## D3 — Reserve `CANONICAL_SHORTCUTS` for actual canonical-fitting rules

- **Prior choice:** Four plausible rivals were declared canonical shortcuts even though each failed one or more labeled canonical pairs.
- **New choice:** Set `CANONICAL_SHORTCUTS = {}` and keep the hypotheses in `SEMANTIC_RIVALS` and/or `LESSON_COMPETITORS` as appropriate.
- **Rationale:** A canonical shortcut has a precise contract: fit every usable labeled canonical pair. Misclassification made the strict semantic gate fail and overstated ambiguity.
- **Alternatives:** Change the rivals until they fit canonical data; rejected because that would manufacture a different hypothesis rather than classify the existing ones honestly.
- **Probe/evidence:** Baseline semantic mismatch examples are retained in `checks/before/result.json`; regression checks every declared semantic rival is refuted by at least one canonical pair.
- **Limitation:** An empty declared shortcut set does not prove no undeclared canonical-fitting shortcut exists.

## D4 — Tie every witness to an executable rival disagreement

- **Prior choice:** `shape_code_1` through `shape_code_4` were presence-only witnesses with no named rival claim.
- **New choice:** Remove those weak witnesses. Retain `target_not_largest`, `target_not_first`, `shape_selector_refutes_fixed_one`, and add `ordered_composition_matters` for reverse order.
- **Rationale:** Presence frequency alone does not show that a lesson teaches anything. A witness should demonstrate a concrete alternative rule producing a different label.
- **Alternatives:** Attach each shape-presence witness to a synthetic fixed-code rival; rejected as redundant because complete shape-code coverage is already enforced by `lesson_identifiable`.
- **Probe/evidence:** Intermediate strict failure in `checks/after-intermediate-weak-witness/result.json`; dedicated red/green regression in `checks/tdd-red-weak-witness/result.json`; final semantic gate reports 4/4 witnesses and claims.
- **Limitation:** The finite rival list cannot establish universal induction.

## D5 — Score reverse transform order without over-rejecting answer-equivalent queries

- **Input choice:** Add `reverse_transform_order` to `LESSON_COMPETITORS` and to the retained semantic witness set.
- **Rationale:** Ordered composition is the task's central noncommutative distinction. A lesson must refute reverse order when the query answer would change; it need not reject a query on which both orders happen to agree.
- **Alternatives:** Require every query to have different forward/reverse outputs; rejected because it unnecessarily shrinks legal support and confuses rule identifiability with one answer-equivalent instance.
- **Probe/evidence:** Four-window regression across difficulties, seeds `0..3`, and starts `0..7`; final production census 300/300 identifiable.
- **Limitation:** Arbitrary held-out rotations can remove the required distinguishing examples, as L1 documents.

## D6 — Keep a four-example ordered curriculum

- **Input choice:** Four consecutive demonstrations, then the next generated pair as query. Seed-derived offsets permute shape/transform identities without breaking coverage.
- **Rationale:** Each window covers all four shape codes and all seven transform codes, while position scheduling includes both target-first and target-not-first examples. This is the minimal declared schedule that directly teaches selector and code meanings.
- **Alternatives:** Three demonstrations; rejected because complete four-shape coverage is impossible. Arbitrary query placement; rejected because the measured rotation census has 135/1,500 ambiguities. Five demonstrations plus a sixth query could support more rotation policies but increases lesson cost and was not needed by the production assembler.
- **Probe/evidence:** `lesson_identifiable`, task-local window regression, after semantic smoke, and `checks/lesson-census.json`.
- **Known limit:** The ordered policy is load-bearing. Downstream assembly must not rotate the query unless it reruns identifiability and resamples failures.

## D7 — Preserve distribution breadth and explicit canonical anchors

- **Input choice:** Keep canonical-profile anchors every fifth sample; use banded dimensions elsewhere; retain two or three disconnected objects, equal-size/larger distractors, distinct colors, and target-position variation.
- **Rationale:** Anchors satisfy profile support without pinning the distribution, while distractor and position schedules attack common size/scan-order shortcuts.
- **Alternatives:** Make every sample canonical-sized; rejected as an unnecessary restriction. Pure random schedules; rejected because short lesson windows could omit required code distinctions.
- **Probe/evidence:** Profile floor exact/envelope 19/60 and per-band exact support 8/20, 5/20, 6/20; diversity/distribution/override stages green.
- **Limitation:** Schedule proofs cover declared competitors and tested starts, not every imaginable shortcut.

## D8 — Prototype composition order as an episode-level parameter, separate from canonical execution

- **Input choice:** Parameter `composition_order ∈ {forward, reverse}`, selected once per episode; `forward` is canonical/default.
- **Rationale:** It is a small rule change with genuine noncommutative behavior, an exact one-fragment Racket delta, and demonstrations that can identify the selected value.
- **Alternatives:** Parameterize shape templates or transform-code permutations; rejected because those would change several semantic interfaces and make a less controlled experiment.
- **Probe/evidence:** `workspace/parametric/prototype.py`, task-local tests, and `checks/parametric/order-prototype/summary.json`; seeds `2` and `0` exercise both settings.
- **Prior implementation changed:** The first prototype used shared `wrap_rule` and failed outside a full repository because of `scripts.comment_solutions`. The current prototype strips `(rule! ...)` and executes the exact callable directly via `RacketBridge`.
- **Limitation:** The prototype searches for distinguishable episodes and is not integrated with production sampling, approval, or curriculum policy.

## D9 — Report rotation failure rather than modifying production around it

- **Input choice:** Retain the exact 300-lesson census and its 1,500 rotated holdouts as diagnostic evidence.
- **Rationale:** Production passed completely, while rotation failures are reproducible consequences of withholding a coverage-bearing pair. Hiding them would overstate data safety; forcing a repair would solve a policy the generator does not claim to support.
- **Alternatives:** Resample every possible rotation or increase demonstrations; viable only if downstream requires arbitrary query positions. That requirement is currently absent.
- **Probe/evidence:** `checks/lesson-census.json`; 0/300 production ambiguity, 135/1,500 rotated ambiguity, with the first exact counterexample retained.
- **Limitation:** Random census is broad but not exhaustive over all seeds or undeclared rivals.

## D10 — Leave adversarial audit targets unchanged

- **Input choice:** Audit `c59d7541b22e` and `df84ec34ba5d` without patching either.
- **Rationale:** Assignment duties make these peer inspections evidence-only. `c59...` has no reproduced defect after schedule enumeration. `df84...` has a concrete inert-control defect for its owner.
- **Evidence:** `AUDIT.md` and source-bound files under `checks/audit/`.
