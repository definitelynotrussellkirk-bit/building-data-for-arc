# Working notes: 8b595f6acd93

## Current decision

Reviewer-reported **ready** native family after a second adversarial pass. This is not owner approval, native acceptance, or training admission.

## Base repair

- Preserved the exact canonical rule and canonical default.
- Separated declared override ranges from difficulty sampling bands; explicit valid controls no longer become invalid merely because the sampled difficulty is narrow.
- Added strict rejection for unknown controls and invalid axis values.
- Repaired the explicit-count contract twice: dimensions grow only when unspecified, and every accepted placement is now checked semantically so intersecting arms cannot create accidental extra centers. `n_pluses` is the exact number of fillable centers.
- The fallback restarts from a complete shuffled lattice and raises rather than silently returning a semantically over- or under-counted grid.
- `self_check` now enforces the declared dimension, palette, count, and non-overlapping-target bounds while continuing to accept canonical partial-plus distractors.

## Native family

- `mode=canonical`: fill every zero cell whose four cardinal neighbors are color 3 with color 4.
- `mode=pair_recolor`: perform the canonical fill, then recompute exact 8-connected color-4 components on the updated grid and recolor only components of size two to color 8.
- Minimum-demo inputs now contain a teaching-complete prefix: an active diagonal pair, an independent orthogonal pair, a trimer, a partial plus, a mismatched-color plus, and a passive true plus.
- Declared rivals include any-uniform-nonzero-arm filling, its pair-recolor extension, diagonal-only pair classification, and identity. All are rejected by every retained two-demo episode in the bounded sweep.
- The executable `wrong_order.rkt` counterfactual classifies pairs before the fill and changes the witness answer. It remains causal evidence, not a promoted teaching hypothesis.
- Contract: 2–6 demonstrations, 1–4 queries; qualification uses 3 demonstrations and 4 distinct queries. The largest retained query is 30×30.

## Current evidence

- Focused staged tests: `checks/8b595f6acd93-tests-round2/result.json` (49 passed).
- Deep contract/teaching audit: `checks/round2-deep-audit-results.json`; 9,472 exact-count axis cases, 512 default cases, 64 minimum-demo episodes, 320 strict rival rejections, and 128 extra Python/Racket equivalence checks for this family.
- Native authoring preflight: `checks/8b595f6acd93/qualification/qualification.json` plus sibling `execution.json` (4 jobs, 2 settings, 40 protected-Racket evaluations).
- Causal witness and replay: `checks/8b595f6acd93/causal/witness.json`, `checks/8b595f6acd93/causal/replay.json`.
- Sequential public projection: 16 content-addressed single-query views; `checks/8b595f6acd93/first-turn.json` records 24 private-field invariance checks.
- Final source/evidence closure: `checks/final-evidence-audit-round2.json`.

## Remaining owner work

Owner source review, native qualification, and fresh acceptance replay remain mandatory. The bounded sweep does not prove universal uniqueness or correctness for every future environment and seed.
