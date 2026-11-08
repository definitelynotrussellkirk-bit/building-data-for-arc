# Working notes: 094e0794786c

## Current selected design (v3.0.0)

**Intended rule.** Find the color-1 and color-2 objects, translate each tight crop to top-left origin, and paint color 8 on the symmetric difference. The output dimensions are the maximum normalized height and width of the two objects; an empty symmetric difference would produce a 1×1 zero grid under the pinned Racket authority.

**Pinned authority.** `RULE_HASH = e94c733a8465`. The selected base Racket `target_code` was synchronized byte-for-byte to its existing `raw_code`; this removed comment-only source divergence and did not alter executable semantics or canonical outputs.

## Reversed baseline choices

The imported v2.2.1 generator treated `split_color`, `one_color`, `no_shapes`, `identical_shapes`, and `full_grid` as ordinary/degenerate texture paths. That mixed disconnected, missing-object, empty-XOR, and full-grid examples into a task whose canonical lesson is two connected objects. It also exposed axes it did not honor, omitted `RULE_HASH`, accepted unknown overrides, used capped retries with a fallback, and had a validator that only required one blue cell.

The selected v3.0.0 design removes those paths. Every generated sample now contains exactly one 4-connected blue object and one 4-connected red object, each with 3–7 cells. Their global placements have Manhattan distance greater than one. After normalization, the shapes must overlap and each must also contribute an exclusive cell. Consequently every individual example refutes normalized union, intersection, blue-only, and red-only shortcuts.

## Distribution and construction decisions

- Declared exact axes are `grid_h=8..12`, `grid_w=9..14`, and `n_cells_1/n_cells_2=3..7`; all 3,000 Cartesian combinations work in every difficulty band.
- Canonical dimensions 8×9, 8×10, and 9×10 receive extra default weight, while every declared value remains reachable in every band.
- Shapes come from a finite deterministic enumeration of connected polyominoes within 4×4 bboxes: sizes 3..7 have 6, 19, 61, 182, and 476 fixed shapes respectively.
- Pair selection and placement enumerate finite candidates. There is no capped retry that can silently shorten an object and no fallback that changes requested axes.
- `observe_overrides` recovers all advertised controls from returned pixels. Unknown keys and non-integer values fail loudly.

## Semantic contract

`strict_canonical_like` is the strengthened validator. `SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`, `WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `lesson_identifiable` cover four concrete alternatives: normalized union, normalized intersection, blue-only, and red-only.

## Final measurements

Generator SHA-256: `21aa14315da3568bdacad323642fd0f74bbd06265d17bba2efbdc212b31ac154`.

- Final after battery: 12/12 green with required query rotations (`checks/after/`).
- Task-local regression suite: 62 passed (`checks/task-tests-final/`).
- Exhaustive task-local axis probe: 3,000/3,000 combinations, zero failures (`checks/domain-probe.json`).
- Profile floor exact hits: easy 8/20, medium 13/20, hard 13/20.
- Semantic census: 600/600 strict-domain draws; both witnesses fired 600/600.
- Lesson smoke: 12/12 ordered lessons and 48/48 query rotations identifiable.
- Larger census: 300/300 lessons and 1,200/1,200 rotations, zero ambiguity or scoring errors across 1,200 unique inputs (`checks/lesson-census-final.json`).
- Racket smoke: 120/120 applications, 108 distinct outputs, no input mutations.

## Known limits and open findings

The finite rival set is not a proof of unique human induction against every imaginable program. Polyomino bboxes are capped at 4×4, so long thin 5–7-cell objects are intentionally absent even though cell-count coverage is complete. Colors remain fixed at canonical roles 1, 2, and 8; no color-role permutation claim is made. Training approval remains a maintainer decision despite green checks.
## Current reviewer considerations

Source SHA-256: `21aa14315da3568bdacad323642fd0f74bbd06265d17bba2efbdc212b31ac154`.

# Decisions for `094e0794786c`

Final generator SHA-256: `21aa14315da3568bdacad323642fd0f74bbd06265d17bba2efbdc212b31ac154`.

## D1: Restore one coherent canonical input domain

**Prior choice.** Version 2.2.1 exposed `plain`, `split_color`, `one_color`, `no_shapes`, `identical_shapes`, and `full_grid` as ordinary or degenerate textures. The rationale was not retained, so it is unknown whether these were intended as robustness examples, diagnostics, or training data.

**Decision.** Remove those texture branches from the selected generator. Every sample now has exactly one connected color-1 object and one connected color-2 object, because that is the compositional structure present in the canonical examples and required by the normalized-XOR rule.

**Rejected alternatives.** Keeping degenerate paths behind a low probability still pollutes lessons with missing operands, empty XORs, disconnected color groups, or full-grid artifacts. Keeping them as advertised exact controls would also require a separate lesson contract and validator semantics; no such curriculum requirement exists here.

**Evidence.** R1; baseline `defect_lint` findings in `checks/before/`; final strict-domain rate 600/600 in `checks/after/checks/094e0794786c_after_semantic_gate.json`.

**Limitation.** This is a deliberate distribution restriction. Robustness to malformed or missing objects is not trained by this generator and should be tested separately, not mixed into the canonical lesson.

## D2: Use finite constructive generation instead of capped retries and fallback

**Prior choice.** The baseline grew/placed shapes through bounded random attempts and could fall back after exhaustion. That made exact controls aspirational rather than guaranteed.

**Decision.** Enumerate a finite bank of fixed 4-connected polyominoes within 4×4 bboxes, select a compatible pair, enumerate legal origins, and choose from feasible placements. A generation request either constructs the exact declared case or raises an explicit error; it never shortens an object or substitutes another case.

**Rejected alternatives.** Raising the retry cap makes silent failure rarer but not impossible. Unbounded retry removes the explicit cap but can hang. Post-hoc repair changes the requested distribution and makes observability difficult to prove.

**Evidence.** R2; 3,000/3,000 exhaustive cases in `checks/domain-probe.json`; shape-bank counts 6/19/61/182/476; final override battery green.

**Limitation.** The 4×4 bbox cap excludes some legal long/thin connected shapes. This was accepted to make finite support, compatible-pair search, and placement guarantees cheap and auditable.

## D3: Advertise only exact controls recoverable from pixels

**Decision.** Keep four exact axes: `grid_h`, `grid_w`, `n_cells_1`, and `n_cells_2`. `observe_overrides` recovers those values directly from the returned grid. Unknown keys, wrong types, and out-of-range values fail loudly.

**Rejected alternatives.** A generic `texture` axis would reintroduce semantic mixtures. Latent difficulty-only knobs are useful for weighting but are not exact controls because they cannot be uniquely recovered from one grid. Declaring known incompatibilities was unnecessary because every Cartesian combination is constructible.

**Evidence.** R2; all 3,000 combinations across four difficulty settings pass `self_check` and exact observation in `checks/domain-probe.json`.

**Failure mode watched.** A future change to shape size or placement must update both `AXES` and the exhaustive probe; otherwise the task test `test_workspace_domain_probe_exhausts_declared_axis_product` fails.

## D4: Weight canonical profiles without removing full support

**Decision.** Favor grid heights 8/9 and widths 9/10, and weight cell counts by difficulty, while retaining nonzero support for every declared value in every band.

**Rejected alternatives.** Narrow per-band hard bounds caused the baseline override conflict. Uniform sampling gave less canonical-profile density and weaker profile-floor margins. Separate band-specific axis declarations would complicate exact-control contracts without improving the task rule.

**Evidence.** Final profile-floor exact hits: easy 8/20, medium 13/20, hard 13/20, in `checks/after/checks/094e0794786c_after_profile_floor.json`.

**Limitation.** These are distribution weights, not a claim that difficulty is psychometrically calibrated. Difficulty changes typical size, not the rule family.

## D5: Make each individual sample refute the main shortcut family

**Decision.** Require the normalized shapes to overlap and to have exclusive cells on both sides. Therefore the authoritative XOR output differs from normalized union, normalized intersection, first-shape-only, and second-shape-only for every generated input.

**Rejected alternatives.** Merely ensuring these witnesses occur somewhere in a batch leaves small lessons vulnerable to schedule accidents. Relying only on the three canonical pairs does not protect generated lessons. A learned-model probe would be expensive and less diagnostic than exact rival functions.

**Evidence.** R5; both witnesses fire 600/600; every declared rival disagrees on the sampled witness checks; `checks/after/checks/094e0794786c_after_semantic_gate.json`.

**Limitation.** Four executable rivals are a targeted adversarial set, not exhaustive program synthesis. Undeclared shape-bank or color-role shortcuts remain possible.

## D6: Strengthen validation rather than trusting the constructor

**Decision.** `self_check` independently verifies rectangularity, integer colors, dimension ranges, palette, exact object-size ranges, one 4-connected component per color, global separation, normalized overlap, and both exclusive regions. Tests mutate lawful grids into missing-color, disconnected, identical, unknown-color, full-grid, singleton, and other impostors.

**Rejected alternative.** Treating `self_check` as a shallow smoke test let off-domain samples certify themselves. Constructor-only assertions would not catch external callers, later refactors, or override bugs.

**Evidence.** R3; initial test-first failures in `checks/task-tests-red/`; final 62/62 in `checks/task-tests-final/`.

## D7: Use three demonstrations and test every query rotation

**Decision.** Preserve `EXAMPLES_NEEDED=3`. Production assembly is three ordered demonstrations followed by one query, and the selected contract additionally supports holding out any one of the four pairs as query. Required rotation checking is enabled in the final battery and large census.

**Rejected alternatives.** Reducing to one or two demonstrations would save tokens but provides little redundancy against undeclared hypotheses. Claiming arbitrary query order from an ordered-only test would be unsupported. Increasing beyond three was not justified because each sample already refutes all declared rivals.

**Evidence.** R5; 12/12 production smoke lessons, 48/48 smoke rotations, 300/300 production census lessons, and 1,200/1,200 census rotations in `checks/lesson-census-final.json`.

**Limitation.** The census rotates within each materialized four-pair lesson; it does not enumerate every possible cyclic sampler start or every rival program.

## D8: Keep canonical colors fixed

**Decision.** Retain role colors 1 and 2 and output color 8. Do not claim color-role exchangeability or add palette permutations.

**Rejected alternative.** Color permutation would be invalid unless the Racket authority and role extractor explicitly transformed semantic roles. Here the rule names colors 1 and 2, so permutation would create a different task rather than harmless augmentation.

**Evidence.** Canonical rule hash `e94c733a8465`; final canonical-pair and Racket smoke checks.

**Limitation.** A model may use fixed colors as role identifiers. That is consistent with this task's rule, not a spurious shortcut within the task.

## D9: Synchronize the selected authority record without changing its rule

**Decision.** Replace selected `target_code` with the record's already-existing `raw_code`, removing comment-only divergence. Do not alter the canonical JSONL row or executable logic.

**Rejected alternatives.** Ignoring the authority-sync failure would leave two selected source renderings. Editing the rule for stylistic cleanup would introduce unnecessary semantic risk.

**Evidence.** R4; before authority-sync report and final green authority check. Executed source SHA remains `1681e7b6bcde91af4810b352bff1f99ca8e36a18d0362e79a78f325c31ce2187`.

## D10: Leave reusable, source-bound reviewer tooling

**Decision.** Add `workspace/domain_probe.py`, which exhaustively walks all declared exact-axis combinations and records shape-bank compatibility. Cover the probe itself in the portable task suite.

**Rejected alternative.** A one-off shell snippet would be harder for future agents to replay and could silently drift from the selected source. Folding this into a global gate would be premature because its shape-bank assertions are task-specific.

**Evidence.** Tool SHA-256 `e86cc0d0e970b538ba1b90b860dcef8d90852a198445b7e0bc0d25d6b59c76a8`; output `checks/domain-probe.json`; final portable task test green.
