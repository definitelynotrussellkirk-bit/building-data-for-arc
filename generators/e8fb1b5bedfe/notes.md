# Working notes: e8fb1b5bedfe

## Review 2026-10-03 — assignment review-7686bbb36c0d13d8

### Baseline findings

The pinned `2.0.1` generator advertised independent grid height, grid width, frame count, and texture controls, but those controls were not truthful.  The completed before battery at `checks/before/checks/e8fb1b5bedfe_before_battery_summary.json` reported 6 green, 2 advisory, and 4 failed stages.  The override gate recorded 9 axis-effect findings, 1 provenance finding, 1,680 generation errors, 6,480 override mismatches, and 8,100 self-check failures; unknown keys were accepted.  Direct probes also reproduced valid `n_frames` overrides that crashed or silently returned fewer frames because `dict.get(..., ctx.draw_int(...))` evaluated the default eagerly and placement stopped after two successful frames.

Defect lint found three declared helpful texture modes that produced no observable change, ordinary-domain degenerate textures, a missing canonical `RULE_HASH`, and selected authority text divergence.  Rule execution parity itself passed: the authority defect was source synchronization, not a semantic Racket error.

### Repair decisions

1. **Truthful exact controls.**  `AXES` now exposes only `scene_profile` (`canonical_12`, `canonical_13`, `canonical_14`) and `n_frames` (2–4).  Unknown keys and invalid values fail loudly.  `observe_overrides` reconstructs both controls from the emitted grid.
2. **Constructive placement.**  A finite backtracking placer either positions every requested frame with a one-cell background gap or raises; it never truncates the requested set.  The curated size rows fit every advertised scene/count combination.
3. **Task-relevant schedule.**  Sample index modulo three chooses `canonical_shape_bias`, `smallest_not_3x3`, or `widest_not_largest`.  The final profile contains a unique width-6 frame that is not largest by interior area.  The default canonical-shape profile always has 3 or 4 frames, so any three consecutive demonstrations contain a middle frame that must remain hollow.
4. **Executable semantics.**  The generator declares witnesses and rivals for fixed-3×3 smallest, widest-is-largest, and fill-all-non-small.  `lesson_identifiable` rejects a lesson if any declared competitor fits all demonstrations.
5. **Authority pin.**  The canonical source is pinned by normalized hash `583ccfcccab0`; selected base `raw_code` and `target_code` are exact canonical text.  No Racket behavior changed.
6. **Independent tooling.**  `workspace/reference_probe.py` independently parses frames and computes intended outputs, validates canonical shortcut fit, tests all cyclic schedule starts, and reports domain limits, actual sampler coordinates, overlapping lesson references, unique inputs, disagreements, and survivor counts.

### Measured final evidence

Generator SHA-256: `994f0203ad5c12371aacf6b64c3d5e15a238b6e58e6567024934f80338e5bcb0`.

- Full after battery: 12/12 green; see `checks/after/checks/e8fb1b5bedfe_after_battery_summary.json`.
- Selected task tests: 59 passed; see `checks/task-tests/result.json` and `checks/task-tests-console.log`.
- Source-bound lesson probe: 120 overlapping 3-demo + 1-query windows per difficulty band, using one deterministic stream per band and all cyclic starts.  Each band generated 123 sample coordinates and 123 unique grids.  No declared competitor survived any lesson, every witness appeared in every 3-demo window, and self-check/strict-profile failures were zero.  The fixed-3×3 shortcut disagreed on 82/123 generated inputs in each band; widest-is-largest disagreed on 42/123 easy, 44/123 medium, and 43/123 hard.  Both shortcuts still fit all 3/3 canonical pairs.  See `checks/e8fb1b5bedfe_review_probe.json`.

### Limits

This is a deliberately bounded teaching manifold, not universal coverage of all lawful rectangles.  Canvases are limited to the three canonical square sizes; frame sides are 3–6; frame count is 2–4; areas are unique; frames are separated; and only colors 0/4 occur in inputs.  Scheduled counterexamples address the strongest obvious canonical-compatible shortcuts but do not prove that every possible learner hypothesis is eliminated.
## Current reviewer considerations

Source SHA-256: `994f0203ad5c12371aacf6b64c3d5e15a238b6e58e6567024934f80338e5bcb0`.

# Decisions for e8fb1b5bedfe

## D1 — Replace misleading axes instead of repairing every legacy combination

**Baseline choice and rationale.**  Version 2.0.1 advertised `grid_h`, `grid_w`, `n_frames`, `texture`, palette, density, and several compatibility aliases.  The original rationale is not recorded; from the source, the apparent intent was broad morphology and generic curriculum-control compatibility.

**Measured failure.**  The before override gate found 16,270 blocking findings: 1,680 generation errors, 6,480 observable mismatches, 8,100 self-check failures, 9 axis-effect findings, and 1 provenance finding.  Unknown keys were accepted.  Direct valid `n_frames` overrides could crash because an eager default draw ran even when the override existed, and placement could silently truncate a requested 3- or 4-frame scene.

**Decision.**  Expose only two exact, observable controls: `scene_profile` for the three canonical canvas sizes and `n_frames` for 2–4 frames.  Reject unknown or invalid controls.  This is smaller but truthful.

**Rejected alternative.**  Preserve every legacy axis and add incompatibility declarations.  That would retain texture names with no semantic effect, multiply invalid combinations, and obscure the task's actual degrees of freedom.

**Probe.**  The focused suite enumerates all 4 difficulty values × 3 scene profiles × 3 frame counts and reconstructs the requested values from each output.  The final override gate reports no findings and rejects unknown keys.

**Limit.**  Consumers expecting the old generic aliases must migrate to the exact controls; this is intentional because the prior contract was false.

## D2 — Use finite constructive placement

**Baseline choice and rationale.**  The prior sampler made bounded random attempts and returned once it had placed at least two frames.  The likely rationale was to avoid generation failure on tight canvases.

**Measured failure.**  Requested 3- and 4-frame examples could be shortened without an error; this made `n_frames` non-observable and weakened middle-frame teaching.

**Decision.**  Use a finite backtracking search over all legal origins, placing larger rectangles first.  Every advertised size/count/profile row is known to fit.  Generation now either places the complete requested set with a one-cell background gap or raises a clear construction error.

**Rejected alternatives.**  Increasing random retries still gives no completeness guarantee.  Falling back to fewer frames preserves output but violates an exact control.

**Probe.**  Exact-control tests and the 120-draw-per-band distribution test found no truncation, no self-check failure, and all frame counts 2, 3, and 4 in each band.

**Limit.**  Exhaustive candidate search is suitable only because canvases and frame counts are small; it is not a universal large-scene placer.

## D3 — Bound the manifold to canonical dimensions and curated frame sizes

**Decision.**  Generate only 12×12, 13×13, and 14×14 canvases, with frame sides 3–6, 2–4 separated frames, and unique interior areas.

**Rationale.**  These dimensions give every band direct canonical-profile support and make every exact control constructive.  Unique interior areas avoid an authority-dependent tie policy not demonstrated by the canonical task.

**Rejected alternatives.**  Arbitrary 9–18 dimensions broaden morphology but do not teach the ranking rule better and complicated exact placement.  Equal-area examples were rejected because the selected Racket source does not define a pedagogically useful tie semantics.

**Probe.**  The final profile-floor and strict-profile stages are green.  `strict_canonical_like` checks the declared limits, while `self_check` separately checks the task law.

**Limit.**  This does not train extrapolation to larger canvases, touching frames, frame sides outside 3–6, or equal areas.

## D4 — Schedule semantic counterexamples rather than relying on random frequency

**Canonical ambiguity.**  All 3 canonical pairs are reproduced by two wrong rules: “the smallest frame is always exactly 3×3” and “the largest frame is the widest.”  Two-frame examples also cannot distinguish “fill the largest” from “fill every non-small frame.”

**Decision.**  Cycle deterministically through `canonical_shape_bias`, `smallest_not_3x3`, and `widest_not_largest`.  The width counterexample has a unique width-6 frame that is not largest by interior area.  The canonical-shape slot always uses 3 or 4 frames, so every three consecutive samples include a middle frame that must remain hollow.

**Rejected alternatives.**  Independent random witness draws can leave unlucky lessons unidentifiable even when pooled witness frequency looks high.  Making every single grid contain every contrast would reduce natural variation and overfit a rigid visual template.

**Probe.**  `workspace/reference_probe.py` tested all cyclic starts in 120 overlapping 3-demo lessons per band.  Every witness appeared in every lesson; no declared competitor survived.  Fixed-3×3 disagreed on 82/123 generated inputs in every band; widest-is-largest disagreed on 42/123 easy, 44/123 medium, and 43/123 hard.

**Limit.**  The schedule refutes three named high-value rivals, not every possible learned heuristic.

## D5 — Add executable, independently checked semantics

**Decision.**  Declare `SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`, `WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `schedule_profile`, and `lesson_identifiable`.  Add a task-local independent geometry oracle and focused tests.

**Rationale.**  Morphological diversity alone cannot show that a lesson identifies the intended rule.  The independent probe prevents the generator's own helper functions from being the sole source of truth.

**Rejected alternative.**  Documentation-only claims are cheap but non-executable; pooled witness counts also fail to test complete lesson windows.

**Probe.**  The semantic gate is green, 59 selected task tests pass, and the source-bound probe reports 0 unidentified lessons across 360 windows total.

**Limit.**  The Python oracle is review tooling, not label authority.  The canonical Racket program remains authoritative.

## D6 — Synchronize authority text without changing behavior

**Baseline.**  Racket execution parity passed, but the selected base record's `target_code` contained comment edits and did not exactly match canonical source; the generator lacked a `RULE_HASH` pin.

**Decision.**  Set `RULE_HASH = "583ccfcccab0"` and make selected base `raw_code` and `target_code` exact canonical source.  No canonical row and no executable rule semantics were changed.

**Rejected alternative.**  Leaving comment-only divergence keeps authority-sync red and makes later source identity ambiguous.  Editing the canonical rule was unjustified because rule smoke and execution parity were already correct.

**Probe.**  Final rule smoke, Racket lint, and authority sync are green; authority sync reports one exact selected group with execution parity PASS.

## D7 — Evidence and prior leads

No prior return was used as a repair lead; `evidence/associated_notes.jsonl` was empty.  The immutable current baseline, canonical pairs, before battery, and direct reproductions determined the repair.  Interrupted before-battery attempts were retained separately and were not counted as completed evidence.
