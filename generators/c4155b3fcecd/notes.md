# Working notes: c4155b3fcecd

## Review diagnosis

The selected v1.2 generator advertised nine controls but implemented only a left-half subset. It omitted `RULE_HASH`, returned degenerate textures rejected by its own validator, and accepted connected markers despite the singleton description. More importantly, all lawful generated inputs put sources on the left, exactly preserving the wrong left-to-right-only shortcut that already fits all four canonical pairs.

Prior return `review-100d2bc82ed31673:v0001` was used only as a lead. Every claimed defect was remeasured against baseline generator SHA-256 `4ce42763d726e83a0c2493291dc4b16aab8372bdea90efeb3cf234a6cde2e4b0` before repair.

## Selected repair

Version 2.0 replaces the false multi-axis surface with twelve observable `scene_profile` values, four per difficulty band. The schedule is `both, left, both, right`; with `EXAMPLES_NEEDED = 2`, every cyclic three-pair window remains bidirectional after any pair becomes the query. One profile per band exactly supports a canonical dimension/nonzero-palette profile.

The validator now accepts all canonical inputs; rejects malformed grids, orthogonally connected markers, axis fixed points, occupied mirror targets, and low-information single-color/single-row/single-distance scenes; and diagnoses errors rather than raising. The canonical Racket authority was not changed and is pinned by `RULE_HASH = e45306d2be09`.

## Evidence

- Baseline: 7 green, 2 advisory, 3 failed (`checks/before/`).
- Final battery: 12/12 green (`checks/after/`).
- Task regressions: 15 passed (`checks/task-tests-green-2/`; final rerun recorded separately).
- Lesson census: 300/300 materialized, 900/900 query rotations, 0 ambiguities, 900 unique inputs (`checks/lesson-census.json`).
- Exhaustive deterministic schedule probe: `workspace/curriculum_probe.py`.

## Limits

The finite rival set tests four plausible shortcuts; it does not prove uniqueness against every computable rule. Ordinary generated inputs intentionally exclude odd-width center-axis fixed points and pre-filled mirror targets because those branches are no-ops or collision semantics rather than useful demonstrations of the copy rule.
## Current reviewer considerations

Source SHA-256: `b25d986d6feca50b61ddc2dfaaa4e7aba8349f65e04eac560c245b81fab7db9c`.

# Decisions for `c4155b3fcecd`

Final generator: version `2.0.0`, SHA-256 `b25d986d6feca50b61ddc2dfaaa4e7aba8349f65e04eac560c245b81fab7db9c`. The canonical Racket authority was not edited; its pinned rule hash remains `e45306d2be09` and the authority-set SHA-256 remains `4617b609b20ec60e3b0def872b4c12b6141a20017f62a830de4008b2ff0892d1`.

## D1 — Treat semantic identifiability, not label correctness, as the primary defect

**Choice.** Repair the distribution so demonstrations establish the bidirectional rule: every nonzero source is retained and copied to the horizontally opposite cell.

**Rationale.** The baseline generator was label-correct on its own samples, but every normal source was in the strict left half. Consequently, `mirror_left_side_only` fit all four canonical pairs and all lawful baseline data. This is a training defect even though Racket outputs are correct.

**Alternatives rejected.** Merely fixing metadata, adding `RULE_HASH`, or strengthening `self_check` would leave the same wrong hypothesis viable. Randomly placing an occasional right-side source was also rejected because pooled frequency does not ensure that each assembled lesson contains a decisive witness.

**Probe.** `workspace/curriculum_probe.py` checks the shortcut against all canonical pairs and all 36 cyclic start/query rotations. The 100-per-band lesson census independently checks assembled lessons.

**Limit.** Four named rivals are finite evidence, not a proof of unique program identification.

## D2 — Replace nine misleading axes with one exact finite `scene_profile` axis

**Choice.** Remove the baseline `grid_h`, `grid_w`, `palette_kind`, `n_seeds`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture` surface. Expose twelve explicit profiles, four per difficulty band, each recoverable exactly from the returned grid.

**Rationale.** The baseline override gate found thousands of mismatches and generation/self-check failures because most advertised axes were dead, aliases, or ignored by degenerate textures. A finite profile is honest: dimensions, marker count, color count, and left/right counts jointly identify the requested value.

**Alternatives rejected.** Implementing every old axis independently would create many impossible or semantically weak combinations and a much larger contract. Keeping decorative aliases would preserve unobservable metadata. Separate numeric axes were not needed for this small task and would weaken round-trip guarantees.

**Probe.** All twelve profiles are generated, validated, and round-tripped in `tests/test_generator.py` and `workspace/curriculum_probe.py`; the final override stage is green.

**Failure mode.** Adding a new profile with a duplicate observable signature would make `observe_overrides` ambiguous. The profile round-trip test catches that.

## D3 — Use a four-slot `both, left, both, right` schedule with two demonstrations

**Choice.** Set `EXAMPLES_NEEDED = 2`. In each band, cycle through both-sided, canonical-profile left-only, both-sided, and right-only scenes.

**Rationale.** A lesson consists of two demonstrations plus one query. For every cyclic three-pair window, removing any one pair as query leaves two demonstrations whose union contains both left and right sources. This kills both directional shortcuts at lesson level, not merely over the whole dataset.

**Alternatives rejected.** Alternating left/right alone fails when one side is held out as query. A random schedule offers no deterministic lesson guarantee. Three or more demonstrations would work but costs more training context than necessary.

**Probe.** The deterministic probe checks all 36 combinations: 3 bands × 4 starts × 3 query choices. The production census checks 900 rotations over 300 lessons and reports zero ambiguity.

**Failure mode.** Changing `EXAMPLES_NEEDED`, schedule order, or lesson-window assembly can invalidate the proof. The cyclic-rotation test is intentionally coupled to all three values.

## D4 — Preserve one canonical structural profile per difficulty band

**Choice.** One left-only profile in each band exactly matches a canonical `(height, width, marker count, distinct-color count)` signature; the other profiles add the missing bidirectional support.

**Rationale.** The repair should broaden semantics without drifting entirely away from official morphology. Canonical-shaped examples also keep difficulty bands recognizable.

**Alternatives rejected.** Making every profile both-sided maximizes shortcut rejection but discards the original support. Making every profile canonical-shaped would sharply reduce diversity.

**Probe.** `test_default_schedule_hits_canonical_profile_and_all_rotations_teach_both_sides` checks both requirements together.

## D5 — Define “singleton” orthogonally, not by all eight neighbors

**Choice.** Reject horizontal/vertical adjacency but permit diagonal adjacency.

**Rationale.** A first implementation treated singleton as eight-neighbor isolation. The focused suite then failed because a lawful canonical input contains diagonally adjacent markers. The actual task geometry requires cells to be separate orthogonal components, not separated under diagonal connectivity.

**Alternatives rejected.** Rejecting diagonal adjacency would exclude official data. Accepting orthogonal adjacency would permit connected marker objects and contradict the sparse-singleton concept.

**Evidence.** The retained failed iteration is `checks/task-tests-green-1/result.json` (14/15); the corrected interpretation passes 15/15 in `checks/task-tests-green-2/result.json`.

## D6 — Exclude center-axis fixed points and occupied mirror targets from ordinary training scenes

**Choice.** No marker may lie on an odd-width center column, and no source may have another input marker at its mirror target.

**Rationale.** Axis markers are no-ops and do not teach copying. Occupied targets introduce overwrite/collision behavior rather than the core duplication rule. Both reduce clarity and caused baseline degenerate textures to contradict the ordinary validator.

**Alternatives rejected.** Keeping these as “helpful textures” was rejected because they consumed lesson slots without improving the core inference and made override dimensions inconsistent. They could be revisited only as explicitly modeled semantic profiles with collision-order tests.

**Probe.** Focused tests construct and reject an axis marker and an occupied mirror pair.

**Limit.** The curriculum intentionally does not teach collision precedence or fixed-point behavior, even though the authority can execute such grids.

## D7 — Require visible diversity inside every ordinary scene

**Choice.** Each generated input has at least two colors, two occupied rows, and two mirror distances, while preserving sparse orthogonal isolation.

**Rationale.** These conditions ensure that first-color-only and nearest-distance-only rules are contradicted by the same scenes used for training, and prevent accidental single-row or single-distance templates.

**Alternatives rejected.** One-color and one-distance scenes are legal under the broad transformation but semantically weak. Keeping them would require a longer lesson schedule to guarantee witnesses elsewhere.

**Probe.** `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, focused tests, and the final semantic census check these conditions.

**Failure mode.** A future profile with too few markers may make the constraints impossible. `_choose_positions` fails explicitly rather than silently relaxing them.

## D8 — Fail closed on malformed inputs and unknown controls

**Choice.** `self_check` returns diagnostics for nonrectangular, out-of-range, empty, connected, axis, colliding, or low-information grids. `generate` raises on unknown difficulty, unknown keys, or unknown profiles.

**Rationale.** Baseline `self_check(None)` raised `TypeError`, and the generator accepted unknown/dead overrides through the old context. A review contract must distinguish invalid data deterministically.

**Alternatives rejected.** Silently ignoring unknown keys makes provenance untrustworthy. Raising from `self_check` makes batch validation brittle; returning errors is the established interface.

**Probe.** Six malformed-input cases and explicit unknown-control cases are in the focused suite.

## D9 — Add an independent Python mirror while retaining Racket as authority

**Choice.** Implement a small `rule_mirror` for fast regressions, rival checks, and lesson assembly; pin the canonical rule with `RULE_HASH` and leave all Racket bytes unchanged.

**Rationale.** Repeated Racket calls are unnecessary for local schedule proofs, but an independent mirror makes semantic tests readable and cheap. Authority synchronization and rule-smoke parity guard against divergence.

**Alternatives rejected.** Importing private runner functions would violate the packet contract. Editing the Racket rule was unnecessary because the defect was entirely in generation and validation.

**Probe.** Final battery stages `rule_smoke`, `racket_lint`, and `authority_sync` are green. The authority-set hash is identical before and after.

## D10 — Declare four executable rivals and bind them to witnesses

**Choice.** Track left-only, right-only, first-color-only, and nearest-distance-only competitors. Mark left-only as the canonical-compatible shortcut, and expose witness predicates for left sources, right sources, multiple colors, and multiple distances.

**Rationale.** These are the simplest plausible restrictions supported by the baseline morphology. Executable competitors let the semantic gate and lesson census score actual predictions rather than prose claims.

**Alternatives rejected.** A prose-only list is not testable. A much larger speculative rival set would add maintenance burden without evidence that it represents likely model shortcuts.

**Probe.** Every declared witness is required to exist and refute each mapped rival. Every one of 300 final lessons refuted every declared rival.

## D11 — Add reusable, source-bound reviewer tooling

**Choice.** Add `workspace/curriculum_probe.py` and focused tests under the selected generator.

**Rationale.** The standard census samples production lessons, but the four-slot proof is cheap enough to exhaust over every cyclic start and query choice. Future agents need a single command that verifies canonical support, exact profile observation, shortcut fit on canonical data, and lesson-level refutation.

**Alternatives rejected.** Leaving the proof only in review prose would make schedule changes difficult to audit. Copying rival names into the probe was avoided; it reads the generator declarations.

**Probe result.** Final source hash `b25d986d…db9c`, 12 profiles, 36 rotations, zero failures.

## D12 — Keep audit findings separate from the selected-task patch

**Choice.** Do not edit `e0650802a8fb` or `5b40e03f0a23`.

**Rationale.** The assignment requests adversarial review only. `e0650802a8fb` had no reproduced issue in the checked scope. `5b40e03f0a23` has a concrete closure-teaching defect, but changing it would violate the selected-task delta boundary.

**Evidence.** See `AUDIT.md` and `checks/audit/`.
