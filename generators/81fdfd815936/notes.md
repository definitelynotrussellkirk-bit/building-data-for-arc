# Current account: `81fdfd815936`

Version `4.0.0`; `RULE_HASH = "320c881d146b"`.

## Intended rule

Extract same-colour nonzero 4-connected objects. For each object, normalize its tight bounding-box mask and test invariance under left-right reflection. Sort the LR-symmetric candidates by `(top_row,left_col)` and return the tight crop of the first candidate.

The selected Racket `target_code` is synchronized to canonical text. This was a comment/text alignment only; archival `raw_code` remains unchanged and rule semantics did not change.

## Domain and production grammar

`self_check` and `strict_canonical_like` accept rectangular 10–12 by 12–14 ARC grids with exactly three separated objects in three distinct nonzero colours, at least one LR-symmetric object, and at least one LR-asymmetric object. This accepts all three canonical pairs, whose symmetric-candidate counts are 1, 2, and 1.

Production deliberately generates exactly two symmetric candidates plus one asymmetric object to teach the underrepresented ordering branch. It alternates two profiles:

- `asymmetric_first_selected_larger`
- `selected_first_selected_smaller`

The alternation reverses both first-object and size-rank cues. The only advertised exact controls are `grid_h` and `grid_w`.

## Lesson policy

`EXAMPLES_NEEDED = 3`; `LESSON_SCHEDULE_PERIOD = 2`. Every three-demo lesson and every hold-one-out rotation must refute the declared rivals `first_object`, `smallest_symmetric`, `largest_symmetric`, and `last_symmetric`. `smallest_symmetric` is explicitly retained as a canonical-fitting shortcut: it fits 3/3 official pairs but is contradicted by generated lessons.

Measured final evidence:

- fixed seed 0: 6/6 schedule-residue lessons, 24/24 pairs, and 24/24 rotations clean;
- random census: 300/300 lessons, 1,200 pairs, 1,200 rotations, 1,200 unique inputs, zero declared-rival ambiguity/warnings/errors;
- focused tests: 33/33 passed;
- after battery: 12/12 stages green.

These are finite declared-rival checks, not a proof of universal identifiability.

## Decision reversal and prior audits

The baseline choice—require exactly one symmetric object and require it to be first among all components—was reversed. It rejected canonical 3/3 and excluded the authority's candidate-order tie-break. The old default distribution also produced one symmetric candidate in 300/300 retained audit samples.

This resolves the actionable findings from `review-52c1368a63326013:v0001` and `review-d5e9ac6d3cd9b2e8:v0001` on current source: canonical 3/3 now pass, production always presents two candidates, and the canonical-fitting smallest-candidate shortcut is refuted in every measured complete lesson and rotation. Their retained artifacts remain historical evidence and were not rewritten.

## Tests and review tool

Task tests are in `tests/test_generator_81fdfd815936.py`. They cover canonical acceptance/mirroring, strict overrides, invalid calls, distribution, schedule rotations, witnesses/rivals, structural impostors, malformed grids, determinism, fresh outputs, and global RNG purity.

`workspace/review_probe.py` is the reusable authoring probe. It reads the generator's actual declarations and reports object/candidate analysis, selected answer, witness firings, rival disagreements, profile balance, validation failures, and output diversity.

## Known limits

The production sampler uses finite shape banks, exact three-object/three-colour scenes, compact canonical dimensions, 4-connectivity, and exactly two symmetric candidates. It does not explore arbitrary object counts, repeated colours, diagonal connectivity, or every possible symmetric mask. Fixed-period coverage is exhaustive only for the declared start residues at seed 0; the larger census is finite and tests named rivals only.
## Current reviewer considerations

Source SHA-256: `059498774150d039259c96b873c071f94c65b1d5292daa2d16339f14e32043e5`.

# Decisions for `81fdfd815936`

Final generator SHA-256: `059498774150d039259c96b873c071f94c65b1d5292daa2d16339f14e32043e5`.

## D1 — Canonical rule and object connectivity

**Choice.** Treat each nonzero colour as a set of same-colour 4-connected components. A candidate is LR-symmetric when its tight bounding-box mask is invariant under horizontal reflection. Return the tight crop of the first symmetric candidate sorted by `(top,left)`.

**Rationale.** This exactly matches all three labelled canonical pairs and the selected Racket authority. Both older audits identified this rule and supplied a canonical two-candidate witness.

**Alternatives rejected.** First object overall, unique symmetric object, largest symmetric object, smallest symmetric object, and last symmetric object. `smallest_symmetric` fits all three canonical pairs, which is why generated lessons must actively refute it.

**Probe/evidence.** Canonical replay and the independent Python oracle are asserted in `tests/test_generator_81fdfd815936.py`; aggregate rule/authority evidence is in `checks/after/`.

**Limits/failure modes.** The interpretation assumes 4-connectivity and tight-mask symmetry. It does not claim that diagonal touching merges objects.

## D2 — Validator domain: exactly three objects and three colours

**Choice.** Require a rectangular 10–12 by 12–14 grid with exactly three separated nonzero 4-connected components in three distinct colours, at least one symmetric object, and at least one asymmetric object.

**Rationale.** This grammar covers every official input while preventing trivial all-background, one-object, same-colour, singleton, and degenerate-bounding-box examples. It keeps the task focused on object selection rather than segmentation ambiguity.

**Alternatives rejected.** The baseline's “exactly one symmetric object, and it must be first overall” validator was reversed because it rejected canonical 3/3. A much broader arbitrary-object-count grammar was also rejected because it adds unrelated segmentation complexity without evidence from the task.

**Probe/evidence.** `self_check` accepts canonical candidate counts `[1,1,2]`; focused tests reject structural impostors and malformed grids.

**Limits/failure modes.** Production does not explore four or more objects, repeated colours across separate components, or dimension ranges outside the canonical profile.

## D3 — Production always carries two symmetric candidates

**Choice.** Generate two LR-symmetric candidates plus one asymmetric object in every ordinary sample, although the validator accepts canonical inputs with one or two candidates.

**Rationale.** The baseline emitted one symmetric candidate in 300/300 sampled defaults and therefore never taught the authority's ordering branch. Concentrating production on the missing branch supplies high-value counterexamples without invalidating official one-candidate inputs.

**Alternatives rejected.** Randomly using one or two candidates was rejected because a three-example lesson could again omit the tie-break branch. Requiring exactly two candidates in `self_check` was rejected because two official examples have only one.

**Probe/evidence.** `checks/review-probe-smoke.json` reports two candidates in 20/20 samples; the larger lesson census records complete declared-rival refutation.

**Limits/failure modes.** The production distribution overrepresents two-candidate scenes relative to the three canonical pairs. That is intentional curriculum repair, not an estimate of the natural task frequency.

## D4 — Two alternating profiles and size-order reversal

**Choice.** Alternate by sample index between:

- `asymmetric_first_selected_larger`: an asymmetric object occurs before the chosen candidate, and the chosen symmetric candidate is larger than the later symmetric candidate;
- `selected_first_selected_smaller`: the chosen candidate occurs first and is smaller than the later symmetric candidate.

**Rationale.** Together they separate the selection predicate (symmetry) from the ordering tie-break `(top,left)` and prevent size rank or first-object rank from standing in for the rule.

**Alternatives rejected.** A single profile with a fixed size relationship was rejected because either smallest or largest would become a stable shortcut. Purely random placement was rejected because it would not guarantee that every three-demo window contains both counterexample directions.

**Probe/evidence.** The schedule-period census covers both residues per band; every three-demo hold-one-out rotation refutes all named competitors.

**Limits/failure modes.** Sample-index parity is a deterministic teaching schedule. The fixed seed-0 schedule census does not certify every seed, though the 300-lesson random census adds wider support.

## D5 — Three demonstrations and query-rotation policy

**Choice.** Set `EXAMPLES_NEEDED = 3`. The intended lesson is three ordered demonstrations plus one query, and all four hold-one-out query positions must remain identifiable against the declared rivals.

**Rationale.** Three demos are the packet default and are sufficient because any three items from the alternating four-item window include both profiles. Requiring rotations prevents an apparent pass that depends on always putting a particular profile in the query slot.

**Alternatives rejected.** Two demos were rejected because a rotated window can lose one size-order direction. Four demos were unnecessary once the three-of-four property was tested exhaustively over the declared period.

**Probe/evidence.** `checks/schedule-census.summary.json` has 24/24 clean rotations; `checks/lesson-census.summary.json` has 1,200/1,200 clean rotations.

**Limits/failure modes.** Identifiability is only measured against four declared rival functions and the gate's searched generic rivals. It is not a proof against all programs.

## D6 — Only two advertised axes

**Choice.** Advertise only exact `grid_h` and `grid_w` controls, valid across all bands at 10–12 and 12–14 respectively.

**Rationale.** These controls are directly observable and independently enforceable. The baseline advertised dead/singleton semantic controls and texture values that either did nothing or crossed into invalid negative fixtures.

**Alternatives rejected.** Keeping `palette_size`, `n_distinct_colors`, `position_bias`, or texture as nominal axes was rejected because their domains were singleton, dead, or incompatible with the intended grammar. Adding many new axes was rejected as unnecessary for this repair.

**Probe/evidence.** Focused tests exercise both dimension extremes in `None`, easy, medium, and hard; the final override stage is green.

**Limits/failure modes.** Difficulty currently changes shape-pool selection rather than dimension bounds. Colour and shape identity remain deterministic keyed randomness, not user controls.

## D7 — Strict call validation and deterministic purity

**Choice.** Reject bools/floats/strings for integer fields, negative sample indices, unknown axes, invalid difficulty tokens, and out-of-range dimensions. Return diagnostics rather than raise from `self_check` on malformed grids. Preserve deterministic fresh outputs and global RNG state.

**Rationale.** The baseline defect lint accepted invalid scalar inputs and had weak malformed-input behavior. Strict boundaries make generated evidence replayable and override failures attributable.

**Alternatives rejected.** Silent coercion was rejected because `True`, `1.0`, and `"1"` are materially different caller errors. Mutating the global RNG was rejected because it makes order-dependent datasets.

**Probe/evidence.** Focused tests cover invalid calls, malformed grids, deterministic replay, object freshness, and global RNG purity.

**Limits/failure modes.** Error text is intended for diagnostics, not a stable public serialization contract.

## D8 — Authority text synchronization

**Choice.** Apply the selected-only authority-sync proposal after confirming behavior parity. Change only executable `target_code`; preserve archival `raw_code`.

**Rationale.** The pre-repair defect lint found a comment-only divergence. Exact selected-source synchronization removes recurring noise while keeping the historical artifact intact.

**Alternatives rejected.** Leaving the drift was rejected because it caused a standing warning. Rewriting archival `raw_code` or canonical data was rejected because neither was needed and would erase provenance.

**Probe/evidence.** `checks/authority-sync-proposal.json` records the narrow JSON pointer; final `authority_sync` and `rule_smoke` are green with execution parity PASS.

**Limits/failure modes.** This decision is textual synchronization, not a semantic rule change.

## D9 — Reusable review probe

**Choice.** Add `workspace/review_probe.py`, which introspects the generator's own declarations rather than copying a rival-name list.

**Rationale.** Future reviewers need a quick way to see component ordering, candidate counts, chosen crop, witness firings, rival disagreement, schedule balance, validation errors, and output diversity without reconstructing ad hoc scripts.

**Alternatives rejected.** A static report was rejected because it would go stale with source changes. A tool importing private runner aliases was rejected because portable staged layouts differ.

**Probe/evidence.** The 20-sample output is retained at `checks/review-probe-smoke.json`.

**Limits/failure modes.** The probe is authoring support, not an authority labeler; aggregate Racket-backed gates remain the source of verification.

## D10 — Prior audit resolution

**Choice.** Treat `review-52c1368a63326013:v0001` and `review-d5e9ac6d3cd9b2e8:v0001` as the leads for this repair, and resolve both reported defects in the current source.

**Rationale.** Both independently reproduced the same mismatch: canonical rejection and no generated two-candidate ordering lessons. The current tests directly encode their counterexamples.

**Evidence.** Final canonical replay accepts 3/3, production has two candidates, `smallest_symmetric` is declared as canonical-fitting and refuted in every measured lesson, and the 12-stage battery is all green.

**Limits/failure modes.** The imported review index remains historical reviewer-reported evidence; this return does not rewrite its archival records.
