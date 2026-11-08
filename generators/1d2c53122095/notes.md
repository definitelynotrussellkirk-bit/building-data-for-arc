# Working notes: 1d2c53122095

## 2026-10-05 review `review-75f0e94a3e3807b9`

The prior return `local-random-12a68cc30d20` was used as a lead. Its linked-profile design and shape-only rival checks remained sound, but its four-profile period exactly matched `EXAMPLES_NEEDED = 4`: every production query repeated demonstration 0's full observable profile. A model could therefore map a known profile directly to its fixed depth instead of transferring the red-marker counting rule.

Version 3.1.0 keeps four demonstrations and expands each difficulty curriculum to six ordered profiles (`outer, intermediate, inner, outer, inner, intermediate`). Every cyclic four-demo window still covers all three rule branches, while the following query is one of two unseen profiles. `lesson_identifiable` now rejects any repeated query profile explicitly, including a fresh layout generated from the same profile.

The global profile enum is intentionally limited to 16 names because the inherited override linter refuses larger literal categorical domains rather than sampling their boundaries. Exact profiles are shared across adjacent bands where useful; difficulty controls curriculum mix, not scene legality. The canonical Racket authority and rule hash `4e070bae635e` were not changed.

Final generator SHA-256: `7bfef1bdd990a287df1b17bbb38061545f95be940601a5e4fb8fb5628317feb7`.

Remaining limits: the semantic census only excludes declared rivals plus exact-profile repetition; it is not a proof against every contextual hypothesis. The selected rule remains literal-color and top-row dependent, so arbitrary palette remapping or D4 augmentation is outside the declared grammar.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `7bfef1bdd990a287df1b17bbb38061545f95be940601a5e4fb8fb5628317feb7`.

# Decisions for `1d2c53122095`

## D1 / R1 — treat the green baseline as insufficient, not as proof of teachability

**Original rationale:** prior return `local-random-12a68cc30d20` replaced independently sampled axes with one linked exact `scene_profile`, making overrides observable and ensuring every four-profile window included outer, intermediate, and innermost branches. That rationale was reasonable for override fidelity and named semantic rivals.

**New evidence:** because the period equalled `EXAMPLES_NEEDED=4`, the production query at offset four repeated demo 0's profile in 300/300 retained lessons. The declared rivals were pure functions of one grid and therefore could not represent the contextual rule “reuse the output behavior from the demonstration with the same profile.” The reusable probe is `checks/profile_repetition_probe.py`; before evidence is `checks/schedule-leak-before-replay.json`.

**Decision:** classify exact-profile repetition as a teaching defect even though every individual label and all named-rival checks were correct.

**Rejected alternative:** leave the schedule unchanged and merely add the profile-copy hook. That would cause every production lesson to be rejected instead of improving the exported population.

## D2 / R1 — preserve four demonstrations; lengthen the period to six

**Choice:** each band now cycles through six unique profiles ordered `outer, intermediate, inner, outer, inner, intermediate`. Production still uses four demonstrations and one query.

**Why:** every cyclic four-demo window contains all three branch classes, while the query at offset four is absent from the four demonstrations. This removes the measured shortcut with no increase in lesson token cost.

**Alternatives considered:**

- **Five demonstrations with the old four-profile cycle:** rejected because a repeated profile would still appear and lesson size would grow.
- **Five unique profiles:** possible, but a four-demo window can make the held-out branch coverage fragile under rotation; six permits two occurrences of each branch class.
- **Random profile sampling:** rejected because deterministic exhaustive cyclic-start coverage is cheaper and replayable; random sampling would need rejection logic and a much larger statistical proof.

**Probe:** `test_every_sliding_curriculum_window_is_identifiable` and `test_production_query_profile_is_new_in_every_cyclic_lesson_window` exhaust all six starts in all three bands. Final contextual counts are in `checks/schedule-leak-after.json`.

## D3 / R2 — make the contextual shortcut part of the task contract

**Choice:** `lesson_identifiable` now emits `query scene_profile repeats a demonstration, permitting a profile-copy shortcut` whenever the query's exact observable profile occurs in a demonstration.

**Why:** schedule tests protect the current sampler, while the hook protects alternate seeds, hand-built lessons, and future assembly code. The regression deliberately uses a different seed for the repeated-profile query so it proves the check is about the semantic profile rather than byte-identical grids.

**Rejected alternative:** compare only exact input hashes. Fresh layout and marker placement can differ while the linked profile—and its fixed branch—remains the same.

**Failure mode:** this check can be too strict for a task where profile repetition is intentional and the repeated profile does not determine the answer-relevant branch. For this task, each named profile includes the selected depth, so the rejection is deliberate.

## D4 — retain linked profiles instead of reopening independent combinatorics

**Choice:** keep one exact observable `scene_profile` axis rather than expose independent dimensions, frame count, gap, depth, and aspect ratio.

**Why:** the prior return's strongest result was exact override fidelity. Recombining axes independently can create impossible scenes or silently clamp accepted values; linked profiles make each accepted override recoverable from the returned grid.

**Mitigation for profile memorization:** within each band, geometries recur at different marker counts/depths, so a geometry-only mapping is contradicted inside complete lessons. The curriculum also retains rectangular, gap-3, and same-shape/different-depth cases.

**Limitation:** the profile vocabulary remains finite. A model trained over many generated episodes may learn generator-specific regularities not represented by the six declared rivals.

## D5 — share exact profiles across adjacent bands to stay inside the inherited checker boundary

**Intermediate failure:** a literal 19-name `scene_profile` domain caused the override-contract linter to treat the categorical axis as unprobeable; `_axis_values` returns no values above 16. Evidence: `checks/lint-attempt1-domain-limit.command.log`.

**Choice:** reduce the global declared vocabulary to 16 names by sharing lawful exact profiles across adjacent difficulty curricula. Difficulty therefore selects a mix of scenes, not exclusive scene legality.

**Rejected alternative:** keep a computed `"|".join(...)` declaration. The static linter could not inspect it (`checks/after-attempt1-lint.command.log`).

**Rejected alternative:** patch the shared checker inside this return. The assignment permits only selected-task source changes; the shared-tool improvement is raised separately as F2 in `FEEDBACK_TO_CODEX.md`.

## D6 / R3 — do not change the canonical Racket rule

**Choice:** leave canonical and bank authorities unchanged; rule hash remains `4e070bae635e`.

**Why:** the defect was lesson assembly, not label semantics. The independent Python mirror matches all five canonical pairs, the final rule-smoke and authority-sync stages are green, and the exposed solve was prepared from the final generator bytes.

**Rejected alternative:** generalize the rule to colors or cue locations. That would alter task semantics rather than repair training quality.

## D7 / R4 — claim only finite, named-rival evidence

**Choice:** require query-rotation identifiability and run the 300-lesson census with all five query positions rotated.

**Measured result:** 12/12 smoke lessons and 60/60 rotations pass the required gate; 300/300 wider lessons and 1,500/1,500 rotations have no declared-rival ambiguity, hook warning, or scoring error. There are 1,310 unique input grids in the final census.

**Interpretation limit:** these results exclude `identity`, `always_outer`, `always_innermost`, `reverse_depth`, `fill_full_target`, `shape_only_depth`, and the explicit repeated-profile condition. They do not prove unique induction against every possible program or contextual learner.

## D8 — preserve failures and add a reusable contextual probe outside production source

**Choice:** retain the red test run, both linter failures, full before/after source-bound censuses, and a standalone profile-repetition analyzer under `checks/profile_repetition_probe.py`.

**Why:** the ordinary semantic census can stay green while a contextual shortcut survives. The probe consumes retained census instances plus exact generator bytes and reports production and rotation denominators, making the failure cheap to replay for future tasks with observable linked profiles.

**Packaging note:** large census reports may be gzip-compressed with a SHA-256/size restoration manifest to satisfy the 25 MiB return limit; compression does not change the underlying evidence.
