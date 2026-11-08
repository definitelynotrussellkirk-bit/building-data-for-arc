# Working notes: cc74d7392ecd

## Current rule and domain

Every nonzero input cell is a colored seed. The authoritative Racket rule preserves the seed and paints its four orthogonal neighbors with the same color, clipping outside the grid. Generated inputs are rectangular 6–10 by 6–10 grids with two or three pairwise-distinct seeds whose plus neighborhoods do not overlap.

The Racket authority was not changed. `RULE_HASH` remains `e685ca8a450d`.

## Review leads used

The associated review `local-random-3b3a3ed2f54a` was used as a lead for the existing four-profile schedule, non-overlap grammar, and boundary-shortcut concern. All claims in this return were remeasured on the pinned baseline and final source.

## Decisions and reversals

- **Prior choice:** clipped profiles used one ordinary edge seed and never emitted corner seeds.
- **Problem:** all five canonical pairs use only interior seeds, so `ignore_boundary_seeds`, `ignore_corner_seeds`, and `ignore_noncorner_boundary_seeds` all fit the canonical demonstrations. A 100-window probe on the prior sampler found the corner rival survived every lesson in every band.
- **New choice:** the two clipped schedule slots each contain exactly one corner seed, one non-corner edge seed, and one interior seed. The two interior slots remain canonical-scale anchors. Every cyclic three-demonstration window therefore contains both one-edge and two-edge clipping evidence.
- **Axis change:** `edge_seed_count` now supports exact values 0, 1, and 2. Value 2 means one corner plus one non-corner edge seed; value 1 means one non-corner edge seed.
- **Control validation:** `seed`, `sample_index`, and all integer overrides now reject booleans, floats, and strings; negative sample indices reject explicitly.
- **Determinism:** placement pools use a fixed role order rather than set iteration, eliminating Python-hash-seed dependence.
- **Portable tests:** tests use `reviewer_support` canonical helpers and root discovery rather than a legacy private helper or fixed parent depth.

## Final evidence

Final generator SHA-256: `393cb44ebc2c9081288823ea3dd05a4bd3e76a6fed26dcc4462509cf0ccfec65`.

- Full after battery: all 12 stages green (`checks/after-final/`).
- Focused task tests: 36 passed (`checks/task-tests-final-v3/`).
- Lesson census: 300/300 lessons materialized, 0 ambiguous production lessons, 0 ambiguous rotations across 1,200 pairs; 1,196 unique inputs (`checks/lesson-census-final.summary.json`).
- Exact saved counterexample: `counterexamples/boundary_shortcut_counterexample.json`, with authoritative Racket receipt in `boundary_shortcut_racket.json`.

## Known limits

The semantic evidence is finite and tests only declared rivals; it is not a proof of unique induction against every possible program. The domain intentionally avoids overlapping plus neighborhoods, repeated seed colors, more than three seeds, and grids outside 6–10. Overlap priority is therefore unspecified. The final source is reviewer-reported and is not catalog-approved by this packet.
## Current reviewer considerations

Source SHA-256: `393cb44ebc2c9081288823ea3dd05a4bd3e76a6fed26dcc4462509cf0ccfec65`.

# Decisions: cc74d7392ecd

## D1 — Preserve the canonical Racket rule

**Original rationale:** the current authority already matches all five canonical pairs and expresses the intended cardinal-plus transform. **Alternatives:** modify the rule or make Python the authority. **Probe:** rule smoke, authority sync, and all canonical-pair focused tests. **Decision:** no rule change; keep `RULE_HASH=e685ca8a450d`. **Failure mode avoided:** silently repairing labels instead of the input curriculum.

## D2 — Use a four-slot curriculum with mixed boundary scenes

**Prior choice:** two interior anchors alternated with clipped scenes having one ordinary edge seed. This covered one-edge clipping but excluded corners. **Measured failure:** `ignore_corner_seeds` fit every canonical pair and survived 100/100 sampled three-demo lessons in every difficulty band.

**Alternatives considered:**
1. Randomly allow corners — rejected because a complete lesson could still omit them.
2. Add separate corner-only and edge-only profiles — workable but would need more demonstrations or a longer schedule.
3. Put a corner, non-corner edge, and interior seed in each clipped slot — chosen because every three-demo window then supplies both clipping classes while retaining an interior full plus.

**Decision:** profiles 1 and 3 are mixed boundary scenes; profiles 0 and 2 remain canonical-scale interior anchors. **Evidence:** exhaustive four-start focused test plus the 300-lesson rotated census. **Limit:** only declared rivals are covered.

## D3 — Give `edge_seed_count` exact, observable semantics

**Original state:** values 0 and 1 only. **Decision:** valid range is 0..2; 0 means all interior, 1 means one non-corner edge, 2 means one corner plus one non-corner edge. All Cartesian combinations with grid size and 2/3 seeds remain constructible. **Probe:** boundary matrix focused test and 8,910-draw override gate. **Failure modes:** two boundary seeds of the same class are rejected by `self_check`; seed neighborhoods remain Manhattan-separated by at least 3.

## D4 — Reject coercible scalar controls

**Original rationale:** `draw_int` coercion was inherited and not documented. **Failure:** defect lint found 117 accepted invalid scalars across call arguments, axes, and bands. **Decision:** require `type(value) is int` for `seed` and `sample_index`, require nonnegative sample indices, and use `draw_int_strict` for every integer axis. **Alternative:** coerce strings/floats; rejected because it makes replay and API contracts ambiguous.

## D5 — Fix deterministic role ordering

**Failure:** an initial implementation iterated `{"corner","edge","interior"}` before shuffling pools, so RNG consumption depended on `PYTHONHASHSEED`. **Decision:** use a fixed tuple order. **Probe:** subprocess test under hash seeds 1, 2, and 101, plus final defect lint. **Limit:** determinism is asserted for the supported Python/runtime contract, not every future dependency version.

## D6 — Keep the non-overlap grammar

**Rationale:** canonical examples use separated singleton seeds, and non-overlap keeps each seed/color contribution legible. **Alternative:** allow overlapping pluses and define priority. Rejected because canonical evidence does not determine overlap priority and it would add a new rule branch. **Known limit:** generated lessons do not teach overlap behavior.

## D7 — Make tests portable and evidence-rooted

**Prior choice:** import a legacy private helper and locate canonical data by fixed parent depth. **Failure:** portable task-test preflight could not import/locate those resources. **Decision:** use `reviewer_support.canonical_pairs`, `canonical_path`, and `find_root`; locate saved counterexamples under the staged root. **Probe:** final isolated portable suite, 36 passed.

## D8 — Stop after convergent evidence

The final source passed all 12 battery stages, 36 focused tests, a 300-lesson rotated census, and an exposed visible-only solve. Further broadening would change the intended domain rather than repair a demonstrated defect. Remaining uncertainty is explicitly limited to undeclared rivals and excluded overlap/repeated-color domains.

## 2026-10-24 parametric prototype

- Added an **unaccepted task-local prototype** with episode-fixed `neighborhood` values `orthogonal` (the exact canonical Racket program) and `diagonal` (seed plus four diagonal neighbors). The production generator, canonical row, rule hash, and approval state are unchanged.
- Inputs are shared across settings and keyed only by seed/split/index. The public API exposes independent counts of 2–6 demonstrations and 1–4 queries; the four-query schedule ends with a substantive 30×30 scene containing 24 separated seeds across all four boundaries.
- Bounded adversarial work found one placement defect: the two-anchor profile continued filling candidates past its requested count. The loop now stops when the target count is already met, and the focused test retains that regression.
- Fresh protected-Racket evidence covers both settings at seeds 0 and 17, three demonstrations and four queries; every episode leaves only its declared setting among the finite rivals and all 28 labels match Racket. Native qualification is source-bound but does **not** approve the variant or admit training data.
- Next action is owner semantic review and explicit acceptance only if this neighborhood family is wanted; otherwise keep it as proposed evidence.
