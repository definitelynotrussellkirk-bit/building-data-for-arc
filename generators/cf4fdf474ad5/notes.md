# Current notes: cf4fdf474ad5

## Intended rule

Treat every 4-connected nonzero component as one cyan/green rectangular patch. Reject components whose bounding-box height is greater than eight. Among the remaining patches, choose the one with the most color-3 cells; break equal-count ties by smaller bounding-box area and then top-left position. Return that component's exact bounding-box crop. The selected authority is pinned by `RULE_HASH = 9316ff1c04fa`.

## Reversal of the imported distribution

The imported sampler used only short rectangles, advertised many indirect controls, relied on count-only validation, and could form fused or no-valid scenes that failed under the canonical authority. That choice also made the canonical height gate and smaller-area tie-break unlearnable. Version `3.0.0` replaces rejection sampling with a deterministic constructive layout of separated complete rectangles and exposes only three exact, observable axes: `grid_h`, `grid_w`, and `n_patches`.

The default four roles are:

1. `large_valid`: valid height and larger area;
2. `tall_invalid`: height nine and more green than the winner;
3. `winner`: valid height and maximum valid green count;
4. `dense_valid`: smaller and denser, but with fewer green cells.

Even sample indices use a unique-count profile. Odd indices use an equal-green tie between the earlier `8×11` patch and the later, smaller `8×9` winner. This directly refutes the strongest canonical-fitting shortcut, `top_left_on_tie`.

## Validation and teaching contract

`self_check` requires rectangular integer grids using only `0/3/8`, exactly three or four separated fully occupied rectangular components, both colors in every patch, valid dimensions, at least one eligible patch, and exact override agreement when metadata is supplied. `rule_mirror` is a diagnostic oracle only; Racket remains label authority.

The generator declares six executable rivals and six linked witnesses. `lesson_identifiable` checks every labeled demonstration and rejects a lesson when a named rival fits all demonstrations but changes the query. Three demonstrations plus one query are assembled from consecutive draws. The alternating schedule makes every three-draw cyclic window contain a tie witness and preserves all other witnesses on every draw.

## Retained exact counterexample

`counterexamples/top-left-on-tie/` is a normal medium draw at `seed=8`, `sample_index=1`. Two valid patches tie at 23 green cells. The earlier patch is `8×11`; the later patch is `8×9`. Canonical Racket returns the smaller `8×9` crop, while `top_left_on_tie` returns the earlier `8×11` crop. The bundle contains input, Racket receipt, metadata, and a regression test.

## Authority synchronization

Canonical semantics were not changed. The selected active `racket_target.target_code` was token-different but execution-equivalent to canonical. The conservative sync helper refused that case, so only `/racket_target/target_code` was manually aligned to the canonical program after execution-parity evidence. Archival `raw_code` remained byte-for-byte unchanged; hashes and the sole changed JSON pointer are recorded in `checks/manual-authority-sync.json`.

## Final evidence and limits

- Final battery: 12/12 green.
- Portable selected-task tests: 51/51 passed.
- Census: 300/300 three-demo/one-query lessons materialized; 1,200/1,200 unique labeled pairs and all 1,200 query rotations had zero ambiguity, hook warnings, materialization errors, or scoring errors.
- The canonical-fitting `top_left_on_tie` rival fits all 5 labeled canonical pairs and was refuted in every sampled lesson in every band.

The sampler deliberately covers a reviewed rectangular subdomain, not arbitrary malformed/fused objects, holes, additional colors, more than four patches, or canvases outside `22..28`. Finite named-rival checks do not prove uniqueness against every possible learned rule. No training approval is asserted.
## Current reviewer considerations

Source SHA-256: `f577c3f69219ac465b9cb03c36352de625653e76d71f3ebff9df78d87093c286`.

# Design and repair decisions for cf4fdf474ad5

## D1 — Treat the selected Racket program as the complete rule

**Choice.** Pin `RULE_HASH = 9316ff1c04fa` and implement the generator around the rule's full ordering: reject height `>8`; maximize absolute green count; break ties by smaller bounding-box area and then top-left; crop the winner.

**Original rationale.** The imported summary described “maximum green” rectangles and mentioned the tie-break, but its distribution did not exercise all clauses. Whether the omitted height-gate coverage was deliberate is unknown.

**Alternatives rejected.** I did not simplify the target to “most-dotted rectangle,” alter the height threshold, or rewrite canonical semantics to match the old sampler. Those would change the task rather than repair its teaching distribution.

**Probe/evidence.** Canonical parity is covered by every labeled pair in `tests/test_review_repair.py`; final authority/rule-smoke gates passed. The post-repair visible-only solver independently recovered the same rule from generated demonstrations.

**Limit.** The Python mirror is only a test oracle; it is not label authority.

## D2 — Replace stochastic placement with four constructive roles

**Choice.** Build complete, separated rectangles in a two-row layout: `large_valid`, `tall_invalid`, `winner`, and optionally `dense_valid` when `n_patches=4`.

**Original rationale.** The imported generator used random rectangles and overlays, presumably for visual variety. Baseline probing showed that its rejection/placement logic could fuse objects or leave no authority-eligible object, and it never generated a too-tall patch.

**Alternatives rejected.** I rejected retry-until-valid random placement because it obscures support, can fail at edge overrides, and makes exact witness frequency difficult to prove. I also rejected hand-enumerated full grids because they would reduce texture diversity.

**Probe/evidence.** `self_check` is called inside every generation. Exact extrema are tested in every difficulty band. Final self-check, distribution, diversity, grammar, override, and profile-floor gates passed.

**Failure mode/limit.** The constructive geometry intentionally covers only three or four rectangular components on `22..28` canvases. It does not claim arbitrary object composition.

## D3 — Expose only three exact, pixel-observable axes

**Choice.** Keep `grid_h`, `grid_w`, and `n_patches`. Validate unknown keys, type, and range before generation; use strict keyed draws; observe dimensions and component count directly from pixels.

**Original rationale.** The imported generator advertised indirect shape, palette, count, density, and position controls. Several were aliases or not reliably recoverable from a generated grid.

**Alternatives rejected.** I did not retain decorative axes merely for metadata compatibility. Exact controls that cannot be observed and tested are misleading. I also did not expose green count as a public axis because it would couple callers to the internal curriculum roles.

**Probe/evidence.** `test_exact_overrides_round_trip_from_pixels`, invalid-key/type/range tests, and the final override gate passed. The first repaired battery found that default `grid_w` never naturally reached 22; a failing test was added, the default canvas cycle was corrected to include `22×22`, and the full suite was rerun.

**Failure mode/limit.** `n_patches=3` omits the dense decoy, so it is lawful but weaker for one named rival than the default four-patch curriculum.

## D4 — Make every ordinary draw teach the height, count, area, order, and crop clauses

**Choice.** Every default scene includes: a height-nine object with more green than the winner; a valid larger-area object; a valid denser object; a winner that is not first; and a non-identity crop.

**Original rationale.** The baseline's all-short objects allowed a learner to ignore the height gate. Distinct random counts alone did not separate absolute count from density/area and did not force the full ordering.

**Alternatives rejected.** I did not rely on rare random counterexamples or one special degenerate texture. A teaching witness needed to be present predictably in complete lessons.

**Probe/evidence.** Executable witnesses are linked to `max_green_any_height`, `highest_density_valid`, `largest_valid_area`, `first_valid`, and `identity`. Tests require all five on every ordinary draw across all bands. The 300-lesson census refuted each rival in every lesson.

**Failure mode/limit.** These are finite named rivals. A model may still find an undeclared correlated rule.

## D5 — Alternate unique-count and equal-count area-tie profiles

**Choice.** Even sample indices use a unique maximum; odd indices use an equal-green tie where the earlier `8×11` object loses to a later `8×9` object.

**Original rationale.** The canonical examples contain an area tie-break but accidentally align “smaller area” with “top-left.” Therefore `top_left_on_tie` fits all 5 labeled canonical pairs and was the strongest plausible shortcut.

**Alternatives rejected.** A tie only in an optional texture or at low random frequency would not guarantee that a three-demo lesson distinguishes the rival. Putting ties on every draw would overrepresent a secondary clause and reduce unique-count anchors.

**Probe/evidence.** The normal-draw witness is retained in `counterexamples/top-left-on-tie/`. Tests enumerate every three-consecutive-draw cyclic window and every query rotation. The census found zero ambiguity in 300 lessons and 1,200 rotations, and refuted the shortcut in 100/100 lessons per band.

**Failure mode/limit.** The schedule is deterministic with period two; correlations with parity are possible, though both profiles share the primary witnesses and labels.

## D6 — Use fully occupied rectangles with randomized green locations

**Choice.** Paint every patch cyan, then sample exact green positions within it. This preserves the authority's component and bbox interpretation while giving texture variation.

**Original rationale.** The imported generator intended cyan rectangles with green overlays. Keeping that visual family supports canonical morphology.

**Alternatives rejected.** Hollow rectangles, holes, diagonal contact, or sparse point clouds were rejected because they create component/bbox ambiguities not needed to teach this rule. Fixed green masks were rejected because they enable position-template shortcuts.

**Probe/evidence.** `self_check` rejects holes, unexpected colors, incomplete rectangles, touching/fused components, and patches missing either color. Determinism/fresh-object/global-RNG-purity tests pass.

**Failure mode/limit.** Green positions are random but counts, dimensions, and role order are scheduled, so the distribution is intentionally structured rather than visually unconstrained.

## D7 — Add strict structural validation instead of count-only checks

**Choice.** Parse 4-connected nonzero components, require complete rectangles, check separation and color set, enforce dimension/count bounds, and verify that authority selection is defined.

**Original rationale.** The baseline validator mainly counted colors/objects and could admit fused or otherwise authority-pathological scenes.

**Alternatives rejected.** I did not treat “Racket ran once” as sufficient validation. Labels can be executable while inputs violate the documented domain or teaching assumptions.

**Probe/evidence.** Malformed/ragged grids, holes, unknown colors, touching objects, and no-eligible-patch cases are covered by focused tests. The final self-check and strict-profile stages passed.

**Failure mode/limit.** The validator describes the selected rectangular subdomain, not every input on which the canonical program happens to return a result.

## D8 — Declare executable rivals, witnesses, and lesson-level identifiability

**Choice.** Add six pure rival functions, six witnesses, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `lesson_identifiable` that validates labels and checks demonstration/query separation.

**Original rationale.** Correct individual labels do not prove that a multi-example lesson teaches the intended rule.

**Alternatives rejected.** Static prose-only hypotheses and per-grid witness frequency were insufficient. A three-demo lesson must be tested as assembled, including alternate query positions.

**Probe/evidence.** Final semantic gate passed. A 100-per-band census with one query and three demonstrations produced 300/300 lawful lessons, 1,200 unique pairs, and zero production or rotation ambiguity/errors.

**Failure mode/limit.** The contract tests declared rivals and a small generic search set; it is not formal identifiability over all programs.

## D9 — Synchronize only the selected active authority field

**Choice.** Copy canonical `program_solution` into `/racket_target/target_code` after the authority checker proved execution parity; preserve `raw_code` exactly.

**Original rationale.** The selected active target was semantically equivalent but token-different from canonical, causing authority-sync and defect-lint failures. The built-in helper deliberately refused a non-format-only rewrite.

**Alternatives rejected.** I did not alter the canonical ledger, edit archival raw code, or weaken the authority gate. Leaving divergent active text would keep the final battery red.

**Probe/evidence.** `checks/manual-authority-sync.json` records before/after file and field hashes, sole JSON pointer, canonical source hash, and raw-code identity. Focused authority, defect-lint, and rule-smoke reruns passed; final battery passed 12/12.

**Failure mode/limit.** This was a manually reviewed synchronization because the shared tool lacks a receipt-producing execution-equivalence path; feedback F1 requests one.

## D10 — Retain compact source-bound evidence and stop after fresh replay

**Choice.** Keep failed/intermediate/final stage records, the exact shortcut witness, portable tests, solve histories, audit reproducer, and a compressed full census with original SHA/restoration metadata.

**Original rationale.** The packet asks for a small return that can be accepted without reconstructing which source version generated which claims.

**Alternatives rejected.** I did not discard genuine failed runs or include duplicate repository/runtime trees. Large JSON reports were compressed rather than summarized away.

**Stopping criterion.** Stop once final source passes the 12-stage battery, 51 portable tests, 300-lesson/1,200-rotation census, both audits are documented, and the exact delta applies to a fresh extraction whose focused tests and source hashes match.

**Remaining limitation.** Passing checks do not grant training approval, and finite testing cannot rule out every shortcut.

## Proposed parametric extension: height threshold

A task-local prototype now varies only the canonical eligibility gate through hidden episode setting `max_height ∈ {5, 8, 9}`. Setting `8` preserves the exact canonical program bytes; settings `5` and `9` replace only the unique `(<= hh 8)` site. The approved production generator is reused as a setting-neutral input sampler, while `generator.py`, `RULE_HASH`, canonical authority, approval state, and training admission remain unchanged.

`workspace/parametric/prototype.py` supplies strict settings/count validation, an independent Python mirror, deterministic separate demo/query streams, public/private evidence projection, and protected-Racket qualification writing. `adapter.py` and `promotion.json` expose the native promotion contract with independent `1..16` demonstration and query counts. The current source inventory is `workspace/parametric/evidence/manifest.json` (SHA-256 `7b8cc79e4d831b6f19d10d256d108bc08a4c945d409e18c758eaaa361cd85a60`); it explicitly records `variant_approved=false` and `training_admitted=false`.

Bounded evidence at `checks/parametric/height-threshold-v1/` contains one episode per setting, each with one labeled demonstration and four distinct queries. Across 45 protected-Racket evaluations, the demonstration left exactly the chosen setting and every query differed under both alternatives. The public-export checker passed all three hash-named visible files, and selected-task tests passed 94/94. This establishes a promotion-ready proposal only for the finite settings, selected four-patch grammar, seeds `0..2`, and recorded counts; owner qualification, acceptance, production integration, and any training decision remain separate.

<!-- arcpuzzles-trainer-ambiguity:start -->
## Current trainer ambiguity follow-up

Claude supplied 2 exact canonical lesson(s) with a proposed alternative rule. Retained privately with source hashes and all stored queries: `evidence/trainer-ambiguity-current/current.json`. These are **open describer flags**, not confirmed wrong labels or failed current parametric qualifications. Check whether the proposed rival fits every demonstration and changes any stored query; distinguish source revisions before repairing. Approval and training state are unchanged.
<!-- arcpuzzles-trainer-ambiguity:end -->
