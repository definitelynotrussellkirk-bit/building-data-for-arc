# Working notes — 9d0a6f959321

## 2026-10-07 — assignment `review-f9b1174f32dba38f`

Baseline generator `2.0.2` had source SHA-256 `989af90a841f5f0ebc2124cf26c78859c133dc2d3a6ed4c539a212d5fd0cbcfb`. It generated lawful individual grids, but it lacked `RULE_HASH`, advertised controls it did not consume, accepted unknown overrides, had no exact pixel observer, and had no executable semantic/lesson contract. A retained four-pair medium lesson at seed `0`, start `3`, gave all three demonstrations exactly one border orange component while the query had three. The reference-lawful rival “recolor only the first border orange component” therefore fit every demonstration and changed the query (`checks/baseline-lesson-shortcut.json`).

Version `3.0.0` replaces rejection-heavy random polyomino growth with bounded constructive placement. Exact controls are `grid_h` 7–12, `grid_w` 9–14, `n_border_components` 1–2, `n_interior_components` 1–2, and `n_distractors` 0–2. Unknown, mistyped, and out-of-range controls fail loudly. The default index schedule cycles canonical dimensions, component-count witnesses, all four single-border sides, and sparse/broad palettes while retaining deterministic seed variation in shape, placement, and distractor color.

Orange shapes are selected from di-/tri-/tetromino and pentomino variants, contain 2–5 cells, and are separated by an eight-neighbor halo. Border orange components are constrained to exactly one requested side and must contain at least one interior cell; this makes whole-component recoloring visible. Distractors use colors outside `{0,3,7}` and sizes 1–3; the first distractor is placed on a border to refute “recolor every border object.” The reserved output color `3` is absent from inputs.

The final semantic contract includes an independent Python mirror, six rivals, six witnesses, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `lesson_identifiable`. `EXAMPLES_NEEDED=3`. The production lesson is three consecutive demonstrations followed by a fourth pair as query; query rotations are also supported. The final 100-per-band census materialized 300 lessons / 1,200 unique pairs and tested 1,200 query rotations with zero declared-rival ambiguity or materialization/scoring errors (`checks/lesson-census.json`). This is finite declared-rival evidence, not proof against every possible hypothesis.

Final generator SHA-256 is `c83691cd2ae376666917d16ff5c9be23c285e2f7401350466e703555b2c02aee`. The completed source-bound battery reports 12/12 green (`checks/after/checks/9d0a6f959321_after_battery_summary.json`); portable task tests report 33/33 passed (`checks/task-tests/result.json`). The semantic gate drew 600 grids, accepted all five canonical inputs, measured 304 strict canonical-like hits (50.67%, declared floor 10%), and found all declared witnesses in every band (`checks/after/checks/9d0a6f959321_after_semantic_gate.json`).

The selected Racket program was not changed semantically. `repo/shared/data/base/solutions/banks/343f662c728a/E112__9d0a6f959321.json` had behavior-equivalent `raw_code` and `target_code` that differed only by one comment. `target_code` now exactly equals `raw_code`; authority sync and execution parity pass. Canonical ledger bytes are unchanged.

The aggregate battery runner stalled after successful stage receipts on several invocations and was resumed without source changes. The final checkpoint summary is complete and green; the interrupted console transcripts are retained separately. Catalog fields still report `approved=false` and `train_safety=unsafe`; promotion is a maintainer/intake decision, not a test side effect.

Remaining distribution limits: fixed semantic colors 7→3, zero background, no corner-touching multi-side target components, bounded sizes/counts, selected polyomino families, and enforced component separation. These are deliberate teachability constraints, not claims that the canonical rule itself is so restricted.
## Current reviewer considerations

Source SHA-256: `c83691cd2ae376666917d16ff5c9be23c285e2f7401350466e703555b2c02aee`.

# Decisions — 9d0a6f959321

## D1 — Preserve the selected semantic rule

**Decision.** Keep the rule “recolor the entire orange (`7`) 4-connected component green (`3`) iff any component cell touches an outer border.” Pin `RULE_HASH="7af38e7dbf07"`.

**Reason.** All five canonical pairs and generated Racket probes support this law. The baseline failure was distribution/contract quality, not a wrong transformation.

**Alternative rejected.** Rewriting the Racket rule or canonical ledger to match the generator. That would invert authority and was unnecessary. The only base-record edit removes a comment so behavior-identical selected sources are byte-exact.

**Probe.** Rule smoke, canonical task tests, independent `rule_mirror`, and authority sync under `checks/after/checks/`.

## D2 — Replace random growth with constructive separated placement

**Decision.** Build a list of role/shape/color specifications, enumerate lawful placements, shuffle them deterministically, and solve the non-overlap problem by bounded backtracking with an eight-neighbor halo.

**Reason.** This makes component counts and border/interior status exact. The old sampler could silently skip optional placements and could not support an exact override contract.

**Alternatives rejected.** (1) Keep rejection sampling and merely raise retry counts: still makes exact joint controls fragile. (2) Draw rectangles only: too narrow and encourages rectangle-specific shortcuts. (3) Permit touching same-color shapes: they merge into one 4-connected object and invalidate requested counts.

**Failure mode/limit.** Dense minimum-size requests can make placement expensive; the chosen small count ranges and 48 construction attempts keep the advertised domain feasible. Exact-domain tests exercise the maximal 7×9, 2+2+2 profile.

## D3 — Advertise only five observable controls

**Decision.** Expose `grid_h`, `grid_w`, `n_border_components`, `n_interior_components`, and `n_distractors`; reject all unknown, mistyped, or out-of-range values.

**Reason.** Every declared control has a direct pixel statistic and is checked by `observe_overrides`. This is more useful than retaining decorative `palette_kind`, `position_bias`, or fixed-value aliases.

**Alternative rejected.** Keep legacy axes for compatibility while ignoring them. Silent acceptance makes curriculum requests untrustworthy and caused the baseline lint/override defects.

**Probe.** `tests/test_generator.py::test_every_advertised_override_is_exact_and_observable`, invalid-key tests, battery override stage, and `workspace/contract_probe.py`.

## D4 — Use a deterministic curriculum schedule plus seed-level variation

**Decision.** For defaults, schedule five canonical dimensions, periodically insert four broader profiles, cycle target/distractor counts, and rotate the first target side by sample index. Use the seeded generator for shapes, exact positions, and distractor colors.

**Reason.** A purely random sampler can produce a lawful corpus but still place all witnesses outside a short lesson window. The schedule guarantees teachable local windows while preserving visual variety.

**Alternatives rejected.** (1) Independent IID defaults: reproduced the baseline three-demo shortcut. (2) Hard-code a single four-example lesson: would overfit layouts and collapse diversity. (3) Make difficulty bands disjoint: unnecessary for this simple rule and risks band-specific shortcuts.

**Probe.** 48-draw per-band task tests, 600-draw semantic gate, 100-lessons-per-band census, and cyclic starts in the contract probe.

## D5 — Require both positive and negative orange branches

**Decision.** Every generated grid contains 1–2 border orange components and 1–2 interior orange components.

**Reason.** The positive branch shows recoloring; the negative branch refutes “recolor every orange cell.” Individual no-op or all-positive grids add little value to this task’s short lessons.

**Alternative rejected.** Retain `no_objects`, `all_interior`, and `full_grid` degenerates as ordinary training examples. They are label-lawful in isolation but weak or misleading without controlled lesson context and were outside the intended canonical grammar.

**Limit.** The sampler does not cover legal rule-domain grids with zero border or zero interior orange. This is an intentional training-distribution restriction, not a validator claim about the Racket program’s total input domain.

## D6 — Make whole-component and color-selection semantics visible

**Decision.** Every border orange component must extend inward. When distractors exist, the first is a non-orange border object. Distractor colors come from `{1,2,4,5,6,8,9}`; input color `3` is reserved.

**Reason.** These choices directly refute “change only edge cells” and “change every object touching the border.” Excluding input green makes changed cells unambiguous.

**Alternatives rejected.** (1) Single-cell border targets: cannot distinguish whole-object from border-cell recoloring. (2) Interior-only distractors: do not test color selection at the border. (3) Random use of output green in the input: semantically legal in some abstractions, but unnecessarily obscures provenance here.

**Probe.** `whole_component_extension` and `border_distractor` witnesses; linked rival disagreements in the semantic report.

## D7 — Use varied but bounded polyominoes

**Decision.** Orange components use rotations/reflections of domino, line/L triomino, S/T tetromino, and V pentomino families; distractors use monomino/domino/L triomino. Components are separated by a one-cell halo.

**Reason.** This avoids rectangle-only shortcuts while keeping construction and independent validation transparent. Sizes 2–5 match the visible canonical scale.

**Alternatives rejected.** Arbitrary random walks can create highly irregular, thin, or accidental near-collisions and complicate exact placement. A much larger polyomino catalog was unnecessary for teaching a border-selection rule.

**Limit.** This is not exhaustive shape support; shape generalization beyond the selected families remains unmeasured.

## D8 — Define a semantic contract at both pair and lesson level

**Decision.** Declare executable rivals for: recolor all orange, border cells only, first border-orange component only, all border objects, horizontal edges only, and vertical edges only. Link each to a witness and test 3-demo-plus-query identifiability.

**Reason.** Correct labels alone do not ensure the intended rule is inferable. The canonical examples themselves allow the first-component-only shortcut, so generated data must kill it.

**Alternative rejected.** A frequency-only witness census. A witness somewhere in the corpus does not establish that each exported lesson contains enough evidence.

**Probe.** Exact baseline counterexample at `checks/baseline-lesson-shortcut.json`; final semantic gate; final required-rotation census; `lesson_identifiable`; cyclic contract probe.

## D9 — Three demonstrations and one query

**Decision.** Set `EXAMPLES_NEEDED=3`; production holds out the fourth consecutive pair. Also support every hold-one-out rotation of the same four labelled pairs.

**Reason.** Three demonstrations are sufficient under the enforced schedule and match the expected ARC lesson scale. Required rotations prevent the contract from depending on a privileged fourth position.

**Alternative rejected.** Two demonstrations. It is easier for a side-specific or single-component rival to survive, and no evidence justified the lower count. More than three would increase token/data cost without addressing a measured defect.

**Probe.** 300 production lessons and 1,200 required rotations in `checks/lesson-census.json`, plus 144 cyclic rotations in `checks/contract-probe-final.json`.

## D10 — Keep a reusable one-command probe and the original source

**Decision.** Add `workspace/contract_probe.py` and retain `workspace/original_generator_v2_0_2.py`.

**Reason.** Future agents can detect contract regressions without reconstructing this review, while the baseline snapshot makes the red tests and counterexample reproducible.

**Alternative rejected.** Rely only on prose or the full battery. The full battery is authoritative but slower; prose cannot catch code drift.

## Known limits

The final evidence is source-hash-bound but finite. It tests the declared rival set, not all computable shortcuts; it does not measure Qwen3.5-9B loss, accuracy, or downstream transfer. The grammar fixes semantic colors/background, excludes corner-touching multi-side target objects, and bounds shape/count/size. The catalog’s `approved=false` / `train_safety=unsafe` state is intentionally unchanged until maintainer intake.
