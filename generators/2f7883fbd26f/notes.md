# Working notes: 2f7883fbd26f

## Review 2026-10-04

Baseline generator SHA-256: `e65b4498b5978ea83e559a08327d34824ef7bd38e4b1b3dd6b0e69d3f94cd15d`.
Final generator SHA-256: `d5b20c0ceb49913daaea833f90e3813c572ec4b71b5526af271a48b2b7b74039`.

The baseline battery failed five stages. Root causes included unbound rule identity, a non-enforcing self-check, advertised overrides that were ignored or clamped, permissive unknown keys, a declared `bg_color` control that did nothing, and selected/archival Racket text drift. The generator was replaced with an exact constructive grammar rather than retry-and-truncate placement.

Key decisions:

- Preserve the selected canonical rule: count all sliding 2 × 2 all-1 windows and emit a five-cell unary bar.
- Pin `RULE_HASH = "6de5b0b7a0a5"` and synchronize only the selected `racket_target.target_code` with canonical authority. Archival `raw_code` remains preserved.
- Honor the complete Cartesian product of exact controls: dimensions 9–12, target count 0–5, decoy count 1–4, isolated-one count 1–4, and isolated-two count 0–4.
- Declare the two strongest canonical-fitting rivals: counting qualifying color-1 components and counting exact isolated 2 × 2 color-1 components.
- Use overlap strips as decisive witnesses. The final three-slot schedule contains two overlap roles and one canonical-separated role so all two-demo windows and all three-pair query rotations are identifiable against both declared rivals.
- Retain canonical-scale 9 × 9 support in every difficulty band while extending size only to 12 × 12.

Final evidence:

- `checks/after-final-r2/`: all 12 battery stages green.
- `checks/task-tests-final-r2/`: 10/10 task-local tests passed.
- `checks/lesson-census-final-r2.json`: 300/300 lessons materialized, 900 unique inputs, 0 production ambiguities and 0/900 rotated ambiguities.
- `checks/lesson-window-probe-final-r2.json`: 450 cyclic windows and 1,350 rotations passed across all bands and schedule starts.
- `checks/lesson-census-final.json`: retained intermediate evidence showing why the earlier one-overlap/two-separated schedule was rejected (150/900 ambiguous rotations).

Limitations: these are finite checks against declared, canonical-fitting rivals; they do not prove universal rule identifiability. The grammar deliberately stays near the canonical palette and scale instead of exploring arbitrary colors or much larger canvases.
## Current reviewer considerations

Source SHA-256: `e860f31354d2e53ec61c963804d28721ade6768e7929347158b12e1d49057c0b`.

# Decisions: `2f7883fbd26f` review `review-afe55a7b702d549b`

## D1 — Re-measure the approved baseline

**Choice.** Treat accepted return `review-3cfd9dfae096e942:v0001` as a lead, not proof. Run the complete before battery on pinned source `d5b20c0…`.

**Why.** Approval history established provenance but not current execution. The before run found a real contract defect despite 11 otherwise-green stages.

**Rejected alternative.** Skipping checks because the generator was already approved would have retained coercive public behavior.

## D2 — Keep the canonical rule and distribution unchanged

**Choice.** Preserve the selected rule, schedule, exact grammar, semantic witnesses/rivals, and `RULE_HASH = "6de5b0b7a0a5"`.

**Why.** Rule smoke, authority sync, canonical outputs, profile support, and lesson teaching all passed. The defect was at the scalar API boundary, not in puzzle semantics.

**Rejected alternative.** Reworking sampling or Racket would enlarge the patch and risk invalidating an already strong, source-bound teaching distribution.

## D3 — Reject malformed integer controls rather than coerce them

**Choice.** Route all six declared integer overrides through `draw_int_strict`; explicitly require literal nonnegative `int` values for `seed` and `sample_index`.

**Why.** `draw_int` intentionally coerces booleans, numeric strings, and floats. That behavior made exact-control provenance ambiguous and let `4.75` behave like an integer request. The same class affected public call indices.

**Rejected alternatives.** Rounding, truncation, accepting integer-valued floats, or accepting `bool` would preserve silent data drift. Duplicating per-axis parsing would be less consistent than the existing strict runtime primitive.

**Evidence.** Red/green records are retained at `checks/development/task-tests-strict-red/`, `checks/development/task-tests-strict-green/`, `checks/development/task-tests-call-scalars-red/`, and `checks/development/task-tests-call-scalars-green/`.

## D4 — Keep the frozen fixture immutable

**Choice.** Restore `tests/test_generator_2f7883fbd26f.py` to assignment SHA `6a141fa3…` and place all new tests in separate task-local files.

**Why.** The packet explicitly marks the baseline root test as a frozen fixture. New coverage belongs in `tests/test_strict_scalar_contract.py` and `tests/test_parametric_target_color.py`.

**Rejected alternative.** Appending regressions to the frozen file would produce a technically passing suite but an invalid review delta.

## D5 — Parameterize the selected object role, not presentation

**Choice.** Build a separate prototype with `target_color ∈ {1,2}`, default 1. Both settings count overlapping sliding windows and use the same unary output; the setting is selected once per episode.

**Why.** Target color is a small meaningful rule parameter that preserves the original reasoning pattern: identify the relevant color, count all sliding `2 × 2` windows including overlaps, encode the count. The default is exactly canonical.

**Rejected alternatives.** Output-color variation is mostly cosmetic; grid size or distractor count changes inputs but not the executed rule; a threshold or non-overlap parameter would replace the core counting semantics rather than create the nearest family member.

**Limits.** Only values 1 and 2 and one retained seed are assessed. The prototype has no production interface or approval.

## D6 — Require demonstrations to identify the episode setting

**Choice.** Use three demonstration inputs whose color-1 and color-2 window counts differ, then one query; compare both finite settings using live Racket outputs without reading query labels.

**Why.** A hidden episode parameter is legitimate only when demonstrations determine it before the query. The retained setting-compatible sets are `[1]` and `[2]`.

**Rejected alternative.** Merely showing that two Racket programs differ on some input would not establish that complete lessons teach which program is active.

## D7 — Preserve both ordered and rotation teaching evidence

**Choice.** Retain the production census (2 demonstrations, 1 query) and require every hold-one-pair-out rotation to refute the declared rivals. Retain the task-local exhaustive cyclic-start probe as a second layer.

**Why.** Correct labels do not rescue an underdetermined lesson. The final evidence covers 300 production lessons/900 rotations plus 450 cyclic windows/1,350 rotations.

**Limit.** These are finite checks against declared rivals and do not establish universal induction.

## D8 — Audit independently and do not patch audit targets

**Choice.** Record findings for `b7d9205dd62d` and `43f15cc63654` in `AUDIT.md` without altering either source.

**Why.** The audit lane is findings-only. Mixing unrelated repairs into the selected task patch would violate assignment scope and make intake harder to reason about.

## D9 — Package only after source-bound replay

**Choice.** Build the return with the supplied builder, replay its exact `source.patch` into a fresh extraction, verify every changed-path hash, and rerun the portable focused tests there.

**Why.** A green working tree is insufficient if the generated patch omits a new file, applies at the wrong root, or produces different bytes. The final replay receipt and fresh-test evidence are recorded in `RESULTS.json` and the opening review brief remains bound to the final generator hash.

## Current overlapping proposal

Retain as an unselected source-bound proposal: current accepted source already has strict integer axes and nonnegative seed/index guards; this older-baseline return removes the negative-seed rejection. Its schedule_profile checks and four-setting window_size/target_color extension need a rebase that preserves that guard and existing target_color prototype. Returned test counts and Racket evidence bind the proposed bytes only, not current source. No approval or current prototype replacement. Retained at `workspace/proposals/review-ceab85b1067d6579/manifest.json`.
