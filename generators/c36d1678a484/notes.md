# Working notes: c36d1678a484

## 2026-10-05 review repair

### Source-bound defect

Imported generator `2.0.1` (SHA-256 `4a086d892d706d276c39e4e23774a30b501ff7de9d44be2c8384d5d391395756`) generated correct labels but taught a much weaker concept. Its ordinary rows did not distinguish the intended predicate `nonzero(row) == [7]` from common alternatives such as “any row containing 7” or “any singleton row.” It also rejected a canonical singleton-non-7 input in `self_check`, advertised overrides that were not exact, accepted unknown keys, and provided no semantic contract.

The immutable before battery retained at `checks/before/` was 6 green, 1 advisory, 5 failed. A test-first reproducer retained at `checks/task-tests-red.log` failed 17 of 26 cases. The failed cases cover canonical acceptance, exact overrides, unknown-key rejection, missing negative witnesses, canonical-profile support, undeclared rivals, and missing lesson checks.

### Selected repair

Selected generator `3.0.0` (SHA-256 `ce409aa0d3b52df2662fdfe89cfb793c829ec1791bb3b56446449096b00f7ce7`) makes each ordinary grid a compact truth table for the row predicate:

1. one or two positive rows with nonzero sequence `[7]`;
2. one partial multi-7 row, refuting `any_seven`;
3. one singleton non-7 row, refuting `any_singleton`;
4. one mixed row with exactly one 7 and another color, refuting `one_seven_anywhere`.

The three rival implementations are declared in `SEMANTIC_RIVALS`, mapped to named witnesses, reused as `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, and checked by `lesson_identifiable`. `strict_canonical_like` delegates to the broader canonical validator instead of enforcing the sampler recipe. The Racket authority and its hash `e987896b90b9...` were not changed.

### Distribution choices

- Minimum height is 5 because two targets plus all three negative row types fit exactly; minimum width is 3 because the multi-7 row must remain partial.
- Every axis combination is constructive, so no incompatibility list is needed.
- `palette_kind` changes the singleton and mixed-row non-7 colors while preserving the semantic lesson.
- Core sampling strongly favors `6x7` plus the mono palette. This restores exact support for a canonical profile without hiding the full override domains.
- Difficulty affects broad-sampling preference only. It never weakens the witness set or changes override validity.

### Verification

- Strict battery: 12/12 green in `checks/after/`.
- Task regressions: 26/26 passing in `checks/task-tests/`; initial 17 failures are retained.
- Override matrix: 22,770/22,770 accepted draws across 253 cases and 3 bands; unknown keys rejected.
- Semantic gate: 600/600 strict draws, every witness fired 600/600, each rival claim held in 60/60 checked cases, 12/12 lessons identifiable, and 0/48 ambiguous rotations.
- Larger lesson census: 300 lessons, 1,200 unique input pairs, 1,200 rotations, no production or rotation ambiguity among declared rivals.
- Canonical profile floor: 37/60 exact-profile hits, 39/60 envelope hits, and 3/3 canonical inputs accepted.

### Remaining limits

The declared-rival checks are finite and task-specific; they do not prove uniqueness against every imaginable program. Each draw is intentionally dense with all three counterexamples, which is excellent for identifiability but less representative of sparse natural ARC instances. Broad draws and exact overrides preserve size/color variety, while core sampling provides the canonical-density anchor.

Imported associated notes remain in `evidence/associated_notes.jsonl`; the prior generator is retained in `workspace/generator-v2.0.1.py`.
## Current reviewer considerations

Source SHA-256: `ce409aa0d3b52df2662fdfe89cfb793c829ec1791bb3b56446449096b00f7ce7`.

# Decisions

## D1 — Preserve the Racket rule; repair the teaching distribution

**Choice.** Keep the canonical authority unchanged and repair only the input generator, validation contract, tests, and task notes.

**Why.** Independent Python reconstruction and 771 prior Racket comparisons already supported the row predicate `nonzero(row) == [7]`; the before rule-smoke and authority-sync stages were green. The defects were missing distinctions, an over-restrictive validator, and false override metadata—not wrong labels.

**Alternatives rejected.** Rewriting the Racket rule would add authority risk without addressing the training-data ambiguity. Encoding outputs in Python was also rejected because labels must continue to come from the canonical runtime.

**Probe.** Before/after authority-sync and rule-smoke evidence is under `checks/before/` and `checks/after/`.

## D2 — Put all three negative row types in every ordinary grid

**Choice.** Every draw contains a multi-7 row, a singleton non-7 row, and a mixed row with one 7 plus another color, in addition to one or two true targets.

**Why.** The imported generator allowed `any_seven` and `any_singleton` to match all sampled ordinary outputs. Making the distinctions probabilistic would still permit ambiguous three-demo lessons; always-present witnesses make every pair independently informative and every query rotation safe for the declared rivals.

**Alternatives rejected.** Keeping negatives only behind explicit `texture` overrides does not help production sampling. Adding just multi-7 and singleton-non-7 rows leaves the plausible `one_seven_anywhere` shortcut. Sampling one random negative type per grid would require schedule-level resampling and still create avoidable ambiguity.

**Failure mode considered.** Repeating the same semantic roles could create positional shortcuts. Rows and columns are randomized, and the regression suite checks semantic features rather than fixed locations.

## D3 — Use the smallest constructive domain, then expose broad exact axes

**Choice.** `grid_h=5..12`, `grid_w=3..14`, `target_rows=1..2`, and four palette kinds.

**Why.** Five rows are the minimum for two targets plus three distinct negative witnesses. Width three is the minimum that permits a partial multi-7 row with at least one background cell. All combinations are legal, so `INCOMPATIBLE_OVERRIDE_COMBINATIONS` is empty.

**Alternatives rejected.** Retaining the old large minimum dimensions would continue to miss canonical profiles. Advertising axes such as texture, palette size, or distinct-color count without exact observable behavior would repeat the original contract defect.

**Probe.** `observe_overrides` recovers every selected value from returned pixels; the matrix checked 22,770 draws.

## D4 — Favor an exact canonical profile without collapsing diversity

**Choice.** A weighted core draws `6x7`, two targets, and the mono palette; one quarter of curriculum-profile tickets enter broad difficulty-aware sampling.

**Why.** The canonical profiles are `(5,6,2)`, `(5,7,2)`, and `(6,7,3)` when background is included. Because every repaired input necessarily contains 0, 7, and at least one non-7 witness color, `6x7` with the mono pair is the feasible exact profile.

**Failed alternative.** The first draft favored `5x7` with three colors, which is inside the envelope but not an exact canonical profile. The official hard-band schedule caught it; `checks/profile-test-red.log` records the failure. Changing the favored height to 6 produced 37/60 exact hits.

**Limitation.** The core is intentionally strong. Broad draws and exact overrides prevent it from becoming the only shape/palette regime.

## D5 — Validate the law manifold, not the sampler recipe

**Choice.** `self_check` accepts rectangular ARC grids with at least one true single-7 target and at least one multi-cell row. `strict_canonical_like` reuses that validation rather than requiring all three generated witnesses.

**Why.** Canonical inputs are lawful even when they do not look exactly like the synthetic recipe. The previous validator rejected the essential singleton-non-7 canonical negative example.

**Alternative rejected.** Requiring exactly one singleton witness, one mixed witness, or the selected palette pair would make a distribution checker masquerade as a rule-domain validator.

**Known weakness.** Mutation sensitivity is modest for transformations that remain lawful inputs; blank grids are rejected 15/15, while color swaps and some row mutations may remain valid. This is appropriate for a law-manifold validator and is reported rather than hidden.

## D6 — Declare executable rivals and lesson identifiability

**Choice.** Implement `any_seven`, `any_singleton`, and `one_seven_anywhere` as pure Python rivals; map them to named witnesses; reuse them for canonical-shortcut and lesson-competitor checks.

**Why.** Natural-language assurances cannot be exercised by the semantic gate. The executable contract lets the gate verify that each witness really causes a rival/authority disagreement and that no declared rival survives all demonstrations.

**Alternatives rejected.** Declaring witnesses without rivals would prove only feature presence. Declaring rivals without per-witness mapping would make a passing sample harder to diagnose.

**Probe.** The semantic gate checked each witness 600/600 and each mapped rival claim 60/60; the larger census checked 300 production lessons and all 1,200 single-query rotations.

## D7 — Build the regression harness before the repair

**Choice.** Add task-local tests for canonical acceptance, exact overrides, invalid keys/types, deterministic witnesses, pinned canonical profiles, rival disagreement, and query rotation.

**Why.** The first run failed 17/26, proving the suite detected the imported defects rather than merely documenting the final implementation. The profile-floor regression was then added and observed failing before the second minimal change.

**Portability.** Tests use `reviewer_support.find_root(__file__)` and `canonical_pairs`, and accept `GENERATOR_UNDER_TEST` for replaying alternate drafts. The old source is retained at `workspace/generator-v2.0.1.py`.

## D8 — Treat difficulty as a preference, never a semantic branch

**Choice.** Difficulty changes broad size/palette weights only. Every band uses the same rule, witness set, exact override domains, and validator.

**Why.** A band-specific semantic omission could create train/evaluation drift. The gate confirms all witnesses fire 200/200 in each band.

**Alternative rejected.** Easier lessons with fewer negative types would be simpler visually but would teach weaker rules.

## D9 — Retain failures and broad verification separately

**Choice.** Keep the immutable before battery, the 17-failure red test log, the pinned-profile failure, the complete after battery, task-test snapshot, lesson census, standalone lint, and repository pytest.

**Why.** This shows causal progression and prevents a green-only report. The task battery remains the source-bound acceptance evidence; the 362-test repository run is broader integration evidence, not a substitute.

## D10 — Stop at finite, explicit claims

The final checks establish correctness over the declared domains, sampled schedules, canonical pairs, and three plausible rivals. They do not establish universal inductive uniqueness, model behavior, or natural-frequency calibration. The remaining limitation is documented rather than converted into an unsupported “solved completely” claim.
