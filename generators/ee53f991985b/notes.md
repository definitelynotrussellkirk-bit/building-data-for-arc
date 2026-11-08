# Working notes: ee53f991985b

## Current rule and source binding

Generator v3.0.0, final SHA-256 `4d71ea90417191524be11aabf67e213180e4e3334a2882cfa55f1ec0b2c93fa4`, pinned to canonical `RULE_HASH = "638445812e80"`.

For each 4-connected nonzero same-color component, compute its bounding box. Fill that bbox with the component color only when the component cells are exactly the bbox border. Leave incomplete frames, solid rectangles, and other non-outline components unchanged.

## Reversed decisions

- **Prior:** negative components were optional (`n_neg` could be zero), so an ordinary 3-demo lesson could show only complete frames. **Now:** every production input includes one complete outline and one connected broken frame. **Reason:** retained audit seed 4, samples 12–15 showed the canonical-fitting `fill_every_component_bbox` rival surviving all demos and changing the query.
- **Prior:** a large public axis set included aliases, redundant/singleton controls, and controls not reliably honored. **Now:** only exact pixel-observable `grid_h` and `grid_w` are advertised; unknown controls reject. **Reason:** baseline lint/override evidence and simpler truthful API.
- **Prior:** `self_check` enforced preferred large-canvas curriculum and rejected all canonical inputs. **Now:** it validates lawful grammar independent of difficulty and accepts 4/4 canonical inputs. **Reason:** legality and sampling preference are separate contracts.
- **Prior:** larger-only sampling gave 0/60 canonical-profile support. **Now:** unoverridden sample indices divisible by four use a 10×12 two-object anchor; other draws remain difficulty-scaled. **Reason:** final profile floor is 19/60 exact and 20/60 envelope without collapsing diversity.

## Teaching contract

`CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS` all name `fill_every_component_bbox`. `SEMANTIC_WITNESSES["broken_frame"]` checks that the rival and pinned-rule mirror disagree. `lesson_identifiable` rejects a lesson when the rival fits all three demos and changes the query.

Minimal reproducer: `counterexamples/broken-frame-shortcut.json`. Supported Racket evidence: workspace `checks/ee53f991985b-shortcut/racket.json`.

Final measurements at the source hash above:

- official battery 12/12 green;
- portable task tests 24/24;
- semantic strict 600/600, witness 600/600, 12/12 lessons, 0/48 ambiguous smoke rotations;
- census 300/300 production lessons and 0/1,200 ambiguous held-out rotations against the declared rival;
- exact-profile 19/60, envelope 20/60.

## Assumptions and known limits

Production uses background 0, distinct colors per constructed object, bbox-disjoint components, rectangles at least 4×4, and negatives consisting mainly of one whole missing side or a solid rectangle. It does not cover nested/touching bboxes, same-color disconnected objects, small partial edge gaps, arbitrary nonrectangular distractors, or alternative backgrounds. The finite rival contract does not prove unique induction against every possible rule; generic census mutations are diagnostic only.

The Racket authority was not changed. A future authority edit requires updating the pinned hash and rerunning the exact counterexample, task tests, semantic gate, census, and full battery.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-586139662c7b0cde:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `9fdf3699ce9a2abae234a8f3ff1002b87dbf51598c45ab5eb6d4134065102842`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted reviewer-reported v3.0 repair at 4d71ea90417191524be11aabf67e213180e4e3334a2882cfa55f1ec0b2c93fa4 removes optional-negative sampling: every production input includes complete and broken frames, retained rival/counterexample/regression, 24 tests and 300 lessons/1200 rotations reported clean against this named bbox-fill rival. Scope limited to this old-source finding; not a new maintainer run.

### Assessment or prior finding

## ee53f991985b

**Reproduced defect — ordinary production-order teaching ambiguity.** The target generator hash is `9fdf3699ce9a2abae234a8f3ff1002b87dbf51598c45ab5eb6d4134065102842`; the supported apply record binds the executed rule hash and source in the evidence. With seed `4`, difficulty `easy`, samples `12..15`, all four inputs pass `self_check`. Demonstrations 12–14 each contain one complete rectangular outline and no broken negative. The plausible rival `fill_every_component_bbox` therefore matches all three canonical outputs. Query 15 contains one complete outline plus one broken frame; the real rule fills only the complete outline, while the rival also fills the broken frame's bounding box, producing a different query answer. Python endpoint outputs match supported canonical Racket on all four inputs.

Evidence: `checks/audit/ee53f991985b/report.json`, raw supported apply output `checks/audit/ee53f991985b/racket.json`, and replay inputs `checks/audit/ee53f991985b/inputs.json`. The generator has no `SEMANTIC_RIVALS`, `WITNESS_RIVALS`, or `lesson_identifiable` contract, so the existing task-local checks cannot reject this lesson. No source was changed.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-586139662c7b0cde-v0001/audit_assets.json), manifest SHA-256 `8c2f484d99fd655bf1feca6001db94b3b97c41d881bd8784810bd3e8c6e09446`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `4d71ea90417191524be11aabf67e213180e4e3334a2882cfa55f1ec0b2c93fa4`.

# Decisions for `ee53f991985b`

Final generator SHA-256: `4d71ea90417191524be11aabf67e213180e4e3334a2882cfa55f1ec0b2c93fa4`.

## D1 — Make the decisive negative witness mandatory (G1)

**Prior choice.** Version 2.3.0 sampled `n_neg` as 0–1 on easy, 0–2 on default, and 1–2 on hard. The apparent rationale was diversity and optional distractors, but this allowed ordinary three-demo windows with no incomplete frame. Placement failure could also erase a requested negative.

**New choice.** Every production input is constructed with one complete outline and one connected frame missing exactly one side before optional extras are attempted.

**Alternatives rejected.** Requiring only one negative somewhere in each four-pair lesson would remain schedule-dependent and fragile under query rotation. Resampling after lesson assembly would hide the source defect and complicate replay. Merely documenting the rival would not teach against it.

**Probe and evidence.** The retained historical seed-4 window is in the prior audit index. The new `broken_frame` witness fires 600/600 semantic draws and the 300-lesson census reports 0/300 production and 0/1,200 rotated ambiguities against the declared rival.

**Failure modes and limits.** A learner can still exploit narrower distribution facts such as disjoint bboxes, unique colors, or whole-side omissions. The repair establishes the intended predicate against the strongest canonical-fitting bbox shortcut; it does not enumerate all possible hypotheses.

## D2 — Keep the authority rule unchanged and mirror its component predicate (G1, G2)

**Prior choice.** The baseline summary described the correct rule, but the generator lacked a pinned `RULE_HASH`, and no executable semantic contract tied the teaching distribution to the exact completeness predicate.

**New choice.** Pin `RULE_HASH="638445812e80"`, provide `rule_mirror`, and declare `fill_every_component_bbox` consistently in `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`.

**Alternatives rejected.** Changing the Racket authority was unnecessary because supported `apply` output already matched the intended rule. Treating solid rectangles as positive would alter the canonical predicate. A prose-only rule description could not power lesson checks.

**Probe and evidence.** The minimal counterexample at `repo/generators/ee53f991985b/counterexamples/broken-frame-shortcut.json` was checked by an independent test oracle and supported Racket application (`checks/ee53f991985b-shortcut/racket.json`). Authority sync and rule smoke are green.

**Failure modes and limits.** The Python mirror is task-local duplicate logic and must be kept synchronized with authority changes. The pinned hash makes drift visible; it does not itself prove semantic equivalence outside tested inputs.

## D3 — Replace the broad advertised control surface with two truthful exact controls (G2)

**Prior choice.** Version 2.3.0 advertised `palette_kind`, `n_frames`, `n_neg`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture`. Several were aliases, singleton labels, redundant, ignored, or incompatible with lawful teaching inputs. The baseline override matrix produced many findings.

**New choice.** Advertise only `grid_h` (7–24) and `grid_w` (10–28), use keyed strict draws for both, expose `observe_overrides`, and reject every unknown/removed key.

**Alternatives rejected.** Keeping diagnostic aliases would increase the matrix without creating observable independent controls. Exact object-count controls would require either weakening the mandatory witness or defining a larger compatibility table. Exact palette controls were not needed for the repair.

**Probe and evidence.** The final override stage is PASS with nine matrix cases and 34,000-plus draw checks in the retained result. Task tests round-trip minimum, canonical, and maximum dimensions in every band and confirm removed keys fail closed.

**Failure modes and limits.** Object count, negative type, and palette remain stochastic and are intentionally not externally controllable. Consumers needing those axes should add a separately tested contract rather than infer them from implementation details.

## D4 — Add deterministic canonical-profile anchors without shrinking the whole distribution (G2)

**Prior choice.** The baseline intentionally moved to larger canvases and its `self_check` rejected every canonical example as too small. That yielded 0/60 exact and 0/60 envelope profile support.

**New choice.** When `sample_index % 4 == 0` and no overrides are supplied, generate a 10×12 two-component scene, which has the canonical three-color profile. Other residues retain difficulty-scaled dimensions and optional objects.

**Alternatives rejected.** Reverting all draws to canonical sizes would reduce diversity. A profile opt-out was unjustified because the task can support canonical shapes safely. Using seed-only anchors would be harder to reason about and replay.

**Probe and evidence.** Final profile floor: 19/60 exact, 20/60 envelope, and at least one exact hit in each band. All 4 canonical inputs now pass `self_check` and `strict_canonical_like`.

**Failure modes and limits.** The anchor is a distribution schedule, not an exact user control. It may create a learnable sample-index correlation in systems that expose indices; exported ARC lessons normally expose only grids. The profile census, not the residue formula alone, is the acceptance evidence.

## D5 — Reserve full bboxes and use bounded placement with deterministic fallback

**Prior choice.** Version 2.3.0 already reserved frame interiors to stop later distractors from being overwritten, but placement used repeated whole-grid scans and could silently fail to place requested objects.

**New choice.** Place the two mandatory boxes in opposite width partitions, reserve every bbox cell, then use bounded random extra placement with a deterministic fallback scan. Optional extras may stop when space is exhausted; mandatory branches cannot disappear.

**Alternatives rejected.** Allowing overlapping bboxes would complicate component semantics and could make outputs order-dependent. Enumerating and shuffling all candidate rectangles had avoidable quadratic allocation cost. Raising on every optional placement failure would reject lawful cramped exact dimensions.

**Probe and evidence.** Focused tests cover 7×10 through 24×28 exact dimensions in all bands. The final test suite runs in roughly 1.2 seconds; the battery distribution, diversity, grammar, and self-check gates are green.

**Failure modes and limits.** The split construction biases the two mandatory objects toward opposite horizontal halves. This is acceptable for the current repair but is a possible positional shortcut for object-role prediction; because each role’s side is randomly swapped, it does not deterministically identify the positive.

## D6 — Accept canonical inputs; validate the law, not a preferred size regime (G2)

**Prior choice.** `self_check` rejected default inputs below area 168 and hard inputs below area 288, conflating curriculum preference with legal task grammar. All four canonical inputs failed.

**New choice.** Validate rectangular integer grids, supported dimensions, at least one fillable exact outline, and pairwise disjoint component bboxes. Difficulty does not change the law.

**Alternatives rejected.** Keeping size checks only in generation would still leave canonical support ambiguous. A permissive validator that accepted no-op inputs would weaken strict support. Requiring the broken witness in `self_check` would reject canonical pairs that are lawful but ambiguous.

**Probe and evidence.** Canonical acceptance is 4/4; 600/600 generated strict inputs pass. The semantic witness is enforced by production generation and lesson checks rather than by redefining canonical legality.

**Failure modes and limits.** `self_check` accepts some lawful inputs outside production support, including complete outlines without broken frames. That distinction is intentional: legal grammar and teachable lesson distribution are separate contracts.

## D7 — Retain a source-bound minimal counterexample and portable regression (G1, G3)

**Prior choice.** The historical audit had a larger four-sample lesson replay, but no compact task-local fixture covered the exact rival disagreement.

**New choice.** Store a 7×10 input with one complete color-1 outline and one color-2 frame missing its right side. The fixture records intended/rival outputs, the first differing cell, generator SHA, and rule hash. The test locates it through `find_root`, so it works in the portable task-test runtime.

**Alternatives rejected.** An inline-only grid would be less useful to future agents. Using `SOURCE.parent` for the fixture failed in the portable runtime because `SOURCE` points to the staged import copy; that failed run is retained as G3 evidence.

**Probe and evidence.** Final portable task tests pass 24/24. Supported Racket output equals the independent intended output and differs from the rival in six cells.

**Failure modes and limits.** The fixture hash is bound to the final generator bytes; future legitimate generator edits must update the fixture deliberately and rerun both task tests and authority application.

## D8 — Treat the lesson census as bounded evidence, not proof

**Choice.** Report both ordered production and every held-out query rotation for the actual 3+1 materializer. Keep the declared-rival verdict separate from generic diagnostic mutation candidates.

**Probe and evidence.** At final source hash, requested starts 0–99 per band produced 300 lessons, 1,200 unique inputs, and 1,200 rotations. The declared rival was refuted in every case. Full evidence is compressed with an original SHA/restoration map.

**Failure modes and limits.** The census does not enumerate all seeds, all future sampler policies, or all possible rules. Generic mutation diagnostics sometimes survive individual support sets; because they were not established as canonical-fitting task-domain rivals, they are documented as an open limitation rather than promoted to a false blocker.
