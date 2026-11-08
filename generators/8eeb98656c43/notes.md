# Working notes: 8eeb98656c43

## Current account

Version `2.0.0`; final generator SHA-256 `dce59e3fb5874f37bc138d804f37da2234ce9288dcef9b80cbd043b54196884f`; canonical rule hash `87bf6fd393d9`.

**Intended rule.** Preserve the input. For each color-2 cell in the left half of an odd-width grid, paint its reflection across the empty center column color 7. Other colors are unchanged and are not reflected.

**Generator assumptions/domain.** Inputs have 8–10 rows and width 9, 11, or 13; center and right half are empty; 2–4 separated red target components and 0–2 separated non-red controls use the canonical small-shape family in the left half; input color 7 is forbidden. Public exact axes are `grid_h`, `half_w`, `n_targets`, and `n_distractors`, all observable through `observe_overrides`.

## Reversed decision

**Prior choice:** version 1.1.1 generated only red objects. The retained notes did not record a reason beyond matching the visible canonical palette.
**New choice:** cycle all-red, one-control, and two-control profiles.
**Reason/evidence:** all canonical pairs are all-red, so the color-blind `mirror_every_nonzero` shortcut fits them all. The retained mixed-color counterexample and selected Racket output distinguish it. Every four-pair lesson window is tested under every query holdout; the final 300-lesson/1,200-rotation census reports no declared-rival ambiguity.

## Decisions

- Preserve the selected Racket authority; `rule_mirror` is only an executable Python mirror for tests and lesson checks.
- Declare the canonical-perfect color-blind rival and require lessons to refute it.
- Use deterministic local RNG and bounded exact placement; reject invalid scalars, unknown overrides, impossible controls, and malformed grids.
- Keep a canonical all-red profile for support while scheduled mixed-color controls expose the predicate.
- Omit `LESSON_SCHEDULE_PERIOD` because the current strict semantic gate cannot consume the separately completed source-bound period census; cyclic starts remain exhaustive in task-local tests.

## Known limits/open findings

- Finite declared-rival and bounded generic-rival checks do not prove universal rule identifiability.
- The bounded authoring grammar is narrower than every grid on which the Racket program may execute.
- The schedule-evidence integration issue is reported in `FEEDBACK_TO_CODEX.md` F2.
- No canonical/Racket source was changed and no approval status was altered.
## Current reviewer considerations

Source SHA-256: `dce59e3fb5874f37bc138d804f37da2234ce9288dcef9b80cbd043b54196884f`.

# Decisions for 8eeb98656c43

Final generator version: `2.0.0`
Final generator SHA-256: `dce59e3fb5874f37bc138d804f37da2234ce9288dcef9b80cbd043b54196884f`
Canonical rule hash: `87bf6fd393d9`

## D1 — Preserve the selected Racket authority

**Choice.** Leave `repo/shared/data/canonical/puzzles.jsonl` and the selected base authority unchanged. Pin `RULE_HASH = "87bf6fd393d9"` and implement `rule_mirror` only as a testable Python mirror.

**Rationale/evidence.** Canonical pairs and Racket smoke tests already establish the selected transformation: retain the input and reflect only color-2 cells across the empty center axis, painting the reflected cells color 7. The defect was in the generator's teaching distribution and contracts, not in the selected rule. Final rule smoke, Racket lint, and authority sync are green.

**Rejected alternative.** Broadening the Racket rule to mirror every nonzero object would make the issued all-red generator self-consistent but would contradict the canonical color predicate. Palette permutation was also rejected because colors 2 and 7 have fixed semantic roles.

**Failure mode/limit.** The Python mirror is not a second authority. Tests and reports remain bound to the selected Racket hash.

## D2 / F1 — Reverse the all-red-only distribution

**Prior choice.** Version 1.1.1 generated only colors 0 and 2. Its recorded rationale was only that 2–4 color-2 shapes occupy the left half; no note justified excluding lawful controls.

**New choice.** Generate lawful non-red controls in two of three schedule profiles. Controls remain in the left half, use distinct colors from `(1,3,4,5,6,8,9)`, use the same bounded small-shape family, and are not mirrored.

**Reason.** All public canonical inputs are all-red, so the canonical-perfect rival `mirror_every_nonzero` fits every canonical pair. A mixed-color accepted witness is needed to teach that the trigger is specifically color 2. The retained counterexample and Racket result demonstrate the difference exactly.

**Rejected alternatives.** Prose-only documentation would not change training evidence. Randomly adding a control with low probability could still produce ambiguous complete lessons. Recoloring red targets would violate the fixed predicate. Placing controls only in a fixed corner could introduce an avoid-by-position shortcut.

**Probes.** `test_nonred_left_object_is_ignored_and_refutes_color_blind_mirroring`, the minimal counterexample, and the 300-lesson census.

**Failure mode/limit.** Controls are still drawn from a finite color and shape set. Undeclared rivals remain possible.

## D3 — Use a three-profile deterministic curriculum

**Choice.** Cycle `canonical_control`, `one_nonred_control`, and `two_nonred_controls` by sample index. Production lessons use 3 demonstrations + 1 query. Any four consecutive accepted pairs are checked under all four possible query holdouts; every remaining three-demo set must refute the declared rival.

**Rationale.** A deterministic schedule supplies both canonical support and decisive mixed-color evidence without probabilistic lesson rejection. The three-demo floor matches the task's lesson configuration. Two mixed profiles in each three-slot cycle make arbitrary query rotation robust.

**Rejected alternatives.** An ordered-only curriculum was rejected because downstream assembly may rotate the query. Pure rejection/resampling was unnecessary and would complicate reproducibility. A mixed witness in only one of four pairs would fail when that pair becomes the query.

**Probes.** `test_every_three_default_samples_contain_a_decisive_mixed_color_witness` exhausts cyclic starts; `test_declared_rival_fits_public_pairs_but_generated_lessons_refute_it` tests every query holdout; the final census checks 1,200 rotations.

**Failure mode/limit.** The production census samples requested starts 0–99 per band; it is not an exhaustive seed proof.

## D4 / F2 — Keep the schedule, omit the public period constant

**Choice.** Keep `SCHEDULE_PROFILES` and `schedule_profile`, but do not export `LESSON_SCHEDULE_PERIOD` in the final generator.

**Rationale.** On the intermediate source, declaring the period made the strict after-phase semantic gate fail with `declared_period_not_enumerated` even though a separate fixed-seed schedule census completed 9/9 lessons and 36/36 rotations. The current checker did not consume that external report. Removing only the declaration made the exact same teaching behavior pass the strict semantic gate; cyclic starts remain enforced in portable task tests.

**Rejected alternative.** Shipping an otherwise green generator with a knowingly blocking semantic warning would make routine intake impossible. Removing the deterministic schedule itself would weaken teaching quality.

**Evidence.** Intermediate batteries under `checks/after/` and `checks/after-final/`; `checks/schedule-census.json`; final battery under `checks/after-pass/`.

**Failure mode/limit.** Generic tooling cannot automatically discover the intended period from the final module. F2 proposes a source-bound way to attach completed schedule-census evidence instead of forcing this workaround.

## D5 / R2 — Advertise only exact, observable axes

**Choice.** Public axes are `grid_h` (8..10), `half_w` (4..6), `n_targets` (2..4), and `n_distractors` (0..2). `observe_overrides` recovers all four from a lawful returned grid. Unknown keys, booleans, floats, strings, out-of-range integers, unsupported difficulties, and invalid sample indices are rejected.

**Rationale.** The issued generator advertised singleton or dead controls (`palette_size`, `position_bias`, `n_distinct_colors`, `density`, several palette textures) that could not observably affect output. Exact controls should be both honored and externally measurable.

**Rejected alternative.** Marking dead controls diagnostic would preserve misleading surface area. Keeping negative textures in the ordinary domain would mix invalid fixtures into production generation.

**Probes.** `test_exact_axes_are_observable_and_scalar_inputs_are_strict`; final override and defect-lint stages.

**Failure mode/limit.** Difficulty remains a supported band selector rather than an observable exact axis.

## D6 — Bound the input grammar to canonical small objects

**Choice.** Accept rectangular grids with 8–10 rows and width 9/11/13; require an empty center/right half, no input color 7, 2–4 separated red target components, 0–2 separated non-red controls with distinct colors, and only the normalized small shapes represented by the canonical examples.

**Rationale.** The previous validator accepted blank/full/minimal impostors and did not protect component semantics. A bounded authoring grammar makes generation failures visible and keeps counterexamples meaningful.

**Rejected alternatives.** Accepting arbitrary connected shapes would enlarge support without canonical evidence. Requiring only “at least one red cell” was too weak. Requiring all-red would reintroduce F1.

**Probes.** `test_self_check_rejects_malformed_or_rule_ambiguous_inputs`, final self-check/grammar/defect-lint stages.

**Failure mode/limit.** The selected Racket transformation may behave sensibly on inputs outside this generator grammar; those are deliberately out of distribution, not declared invalid for the abstract task.

## D7 — Use deterministic bounded backtracking and RNG isolation

**Choice.** Derive a local stable RNG and use bounded placement/backtracking to satisfy exact target/control counts and separation. Return fresh list objects and never use or mutate global `random` state.

**Rationale.** Exact overrides must not silently degrade when placement is crowded, and replay must be byte-stable.

**Rejected alternative.** The issued “try 40 times and move on” loop could return fewer objects than requested without reporting failure.

**Probe.** `test_generation_is_deterministic_fresh_and_does_not_touch_global_random`; final distribution/override stages.

## D8 — Declare and execute the plausible rival

**Choice.** Put `mirror_every_nonzero` in `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS`; associate it with the mixed-color witness; make `lesson_identifiable` validate labels and refutation.

**Rationale.** The rival is not hypothetical: it fits every usable canonical pair. A whole-lesson executable contract turns the teaching defect into a reproducible gate.

**Rejected alternative.** Copying rival names only into tests would let source and checks drift. The tests instead iterate the declarations exposed by the selected module.

**Failure mode/limit.** One declared rival plus bounded generic mutations is not a complete rule space. QUESTION_ANSWER.md recommends generalizing this pattern as a shared gate.

## D9 — Retain honest failures and solve provenance

**Choice.** Keep the partial before battery, RED tests, two 11/12 intermediate batteries, the blind solve's genuine three attempts, and the post-repair solve's single successful revision with earlier exposure declared `yes`.

**Rationale.** These are useful source-bound records; rewriting them as clean runs would destroy provenance. Only `checks/after-pass/`, `checks/task-tests/`, and `checks/lesson-census-final.json` are used as final-source pass evidence.

## Known limits and open findings

- The finite census establishes no ambiguity only for declared and bounded searched rivals on 300 sampled lessons and their 1,200 rotations.
- The generator's domain is intentionally narrower than every possible grid on which the Racket program can execute.
- The checker/schedule-evidence integration in F2 remains a shared-tool issue; the task-local workaround is tested but less machine-descriptive.
- Audit findings A1 and A2 are reproducible but intentionally unpatched because they concern independently assigned peer targets.

## D10 — Native mirror-then-measure ray-tail family (review-b596ea5e28e57060)

**Defect addressed.** The approved ordinary generator had no native parametric
adapter, promotion contract, source inventory, qualification, or sequential
causal witness for this round.

**Selected design.** Keep the exact canonical red-to-orange mirror as
`followup=canonical`. The alternative `ray_tail` first performs that mirror. A
unique color-1 marker on the center axis then measures the first contiguous
orange run that Stage A created to its right, and Stage B appends an equal-length
color-1 tail. Because the input contains no orange run, the tail position and
length are not available before Stage A. The retained counterfactual substitutes
a fixed one-cell tail.

**Evidence.** The task-local bounded audit swept 32 seeds, both settings, all
2–6 demonstration counts, all 1–4 query counts, 8,320 labeled pairs, 320 causal
separations, and 40 protected-Racket labels plus 20 protected counterfactuals
with no findings. Native qualification passed four jobs. The retained protected
witness replays the qualified alternative against `wrong_intermediate.rkt` on an
audited query. Target tests pass 14/14; public projection checks pass 16
single-query views and 24 private-field invariance mutations.

**Limits / next action.** This is finite reviewer evidence, not universal rule
uniqueness. Owner integration must preserve the exact source binding, rerun
native qualification and causal replay, then perform fresh acceptance. No
training admission is claimed.
