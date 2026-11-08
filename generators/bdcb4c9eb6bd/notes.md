# Working notes: bdcb4c9eb6bd

## 2026-10-07 review `review-450aec7fa7739013`

The baseline source hash was `acf88b5cb5aee7e524a4cec4dcafb43d75a2d8356c2671ddc00b2297cb02e755`. A prior audit in `evidence/review_index.json` was used as a lead, then remeasured against this packet: the validator rejected official border-touching examples, strict canonical-profile support was absent, the advertised controls were mostly ineffective, no executable semantic contract was declared, and the selected rule text diverged from canonical authority.

Version `2.0.0` replaces the loosely advertised axes with two exact controls:

- `scene_profile`: `7x9|11x9|11x10|11x15`
- `background`: `0|3|4|5|6|7|8|9`

Generation is constructive. It creates one to three separated one-gap color-1 rectangular outlines, deliberately permits legal border contact, and cycles the primary object through `canonical_4x4`, `wide_4x5`, and `tall_5x4`. Every consecutive three-example lesson therefore contains a counterexample to the strongest canonical-fitting size shortcut, `four_by_four_only`.

`self_check` now accepts all canonical inputs and rejects malformed/ragged grids, invalid palettes, merged objects, incorrect outlines, corner or multiple gaps, and unsupported profiles. `strict_canonical_like`, `observe_overrides`, executable intended/rival functions, witnesses, lesson competitors, and `lesson_identifiable` form the semantic contract.

The selected base solution's `racket_target.target_code` was synchronized byte-for-byte to canonical `program_solution` (`c507f6de75fe`). The archival `raw_code` was intentionally retained; both executable forms solve all canonical pairs.

Final generator SHA-256: `74d53ab4ff66c8067fecd04bbabdeecc99eb1e489723735ac01bd6b7ca49bef4`.

Evidence:

- `checks/after/checks/bdcb4c9eb6bd_after_battery_summary.json`: 12/12 green.
- `checks/task-tests/result.json`: 81/81 task tests passed.
- `checks/lesson-census.json`: 300 lessons, 1,200 query rotations, zero ambiguities/errors.
- `checks/bdcb4c9eb6bd_reference_probe_racket.json`: independent mirror and 37/37 real-Racket parity checks.
- `checks/shortcut/bdcb4c9eb6bd/counterexample.json`: exact canonical-shortcut witness.

Limits: the semantic evidence is finite and targets declared/plausible rivals; it is not a proof of unique induction against every imaginable hypothesis. The ordinary distribution intentionally stays on the four canonical canvas profiles rather than claiming support for every lawful grid size.
## Current reviewer considerations

Source SHA-256: `74d53ab4ff66c8067fecd04bbabdeecc99eb1e489723735ac01bd6b7ca49bef4`.

# Decisions for `bdcb4c9eb6bd`

## D1 — Treat the prior return as a lead, not as current evidence

**Original rationale:** unknown; the prior audit text was imported in `evidence/review_index.json` and named the border-margin and battery defects.

**Decision:** rerun the pinned source before editing. The fresh baseline reproduced 6 blocking stage failures plus one advisory under generator hash `acf88b5cb5aee7e524a4cec4dcafb43d75a2d8356c2671ddc00b2297cb02e755`.

**Alternative rejected:** cite the earlier return directly. That would not establish the state of this packet or bind claims to the selected baseline.

**Probe:** `checks/before/checks/bdcb4c9eb6bd_before_battery_summary.json`.

## D2 — Use exact canonical canvas/palette profiles

**Input choice:** `scene_profile ∈ {7x9, 11x9, 11x10, 11x15}` and `background ∈ {0,3,4,5,6,7,8,9}`.

**Rationale:** these are the complete canvas/background profiles observable in the canonical pairs. They satisfy the profile floor and avoid claiming unverified canonical support for arbitrary sizes. Every profile remains explicitly overrideable in every difficulty band; difficulty changes weights rather than legal support.

**Alternatives considered:**

- Keep `grid_h` and `grid_w` as independent broad controls. Rejected because the baseline advertised values it did not honor and produced no exact canonical-profile hits.
- Use only one canonical profile. Rejected because it creates an unnecessary size shortcut.
- Expand to every rectangular canvas. Rejected as unsupported by canonical evidence and unnecessary for the repair.

**Failure mode/limit:** exact profiles narrow canvas diversity. The generator compensates with object count, placement, border side, gap, background, and shape variation, but does not claim arbitrary-canvas coverage.

## D3 — Permit border contact and validate the actual law

**Input choice:** the primary rectangle deliberately touches top, bottom, left, or right according to the schedule phase; secondary rectangles may be placed elsewhere while remaining separate.

**Rationale:** canonical examples include border-touching rectangles, and the Racket rule is lawful there. The baseline's mandatory one-cell margin was a validator invention.

**Alternative rejected:** preserve a margin for easier construction. That keeps the reproduced canonical-domain defect and prevents the generator from teaching edge clipping.

**Probes:** all four canonical inputs pass the final validator; 400/400 independent sampled inputs touched a border; real Racket parity passed 37/37 retained cases.

**Failure mode addressed:** a gap at an already-touched edge can produce a zero-length exterior beam. This is still lawful: the interior fills, and clipping at the grid edge is the intended behavior.

## D4 — Make object-size teaching deterministic, not merely probable

**Input choice:** period-three profiles `canonical_4x4`, `wide_4x5`, `tall_5x4`; `EXAMPLES_NEEDED = 3`.

**Rationale:** all canonical rectangle bboxes are 4×4, so the strongest plausible shortcut is “apply the transform only to 4×4 objects.” Randomly emitting a non-4×4 witness does not ensure that every lesson contains one. A deterministic cycle guarantees that every consecutive three-example lesson contains two witnesses, regardless of cyclic start.

**Alternatives considered:**

- Pure random sizing. Rejected because witness frequency is not lesson-level coverage.
- All non-4×4. Rejected because retaining a canonical-shaped case makes the intended generalization clearer and preserves direct canonical resemblance.
- More than three demonstrations. Rejected as unnecessary after exhaustive cyclic-start tests and the 300-lesson rotation census.

**Probes:** task tests enumerate every cyclic three-demo start; semantic gate passes 12/12 lessons and 48 rotations; larger census passes 300/300 production lessons and 1,200/1,200 rotations against declared rivals.

**Limit:** this defeats the declared size shortcut but not every conceivable rival.

## D5 — Construct layouts instead of retrying random placements

**Input choice:** one object on 7×9, up to two on 11×9/11×10, and up to three on 11×15; vertical or horizontal stacking reserves at least one background row/column between components.

**Rationale:** constructive placement makes every legal profile terminate, keeps components separate, preserves the scheduled primary size, and makes border cases deliberate. Difficulty controls density: easy is mostly one object, medium mostly two, hard uses profile capacity.

**Alternative rejected:** baseline-style random retry loops. Those obscure support, can silently fall back, and make exact overrides or schedule guarantees difficult to prove.

**Measured distribution:** in 100 independent draws per band, multi-object counts were 11 easy, 67 medium, and 93 hard; default was 39. No construction crashes occurred in 600 semantic-gate draws or 300 census lessons.

## D6 — Reduce controls to what can be exactly observed

**Input choice:** advertise only `scene_profile` and `background`; reject unknown keys and invalid types/values.

**Rationale:** the baseline's ten-ish controls included aliases, fixed/no-op values, and degenerate textures that did not describe ordinary lawful training data. Exact controls are better than a large misleading surface.

**Alternatives considered:** repair every old axis. Rejected because several were not meaningful independent degrees of freedom, and degenerate controls conflicted with the validator/teaching contract.

**Probe:** final override stage is green; task tests cover every profile/background in every band, observability, unknown keys, type errors, and invalid values.

**Limit:** callers relying on undocumented baseline axes will receive explicit errors rather than silently different behavior. This is intentional.

## D7 — Declare executable semantics and the strongest rival

**Input choice:** keep a Python intended mirror only for checking; declare `SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`, `WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `lesson_identifiable` around `four_by_four_only`.

**Rationale:** labels being correct does not make a lesson teachable. The shared semantic gate and census need executable hypotheses, not prose-only claims.

**Alternative rejected:** rely on output diversity or visible non-4×4 frequency. Neither checks whether the rival actually fits canonical pairs or is refuted in each lesson.

**Probe:** `four_by_four_only` fits 4/4 canonical pairs, disagrees with the exact retained witness, is refuted in 100/100 lessons per band, and survives zero held-out rotations in the 300-lesson census.

**Limit:** the Python mirror is not training authority. Racket remains authoritative, and parity is separately checked.

## D8 — Synchronize selected authority, preserve archival text

**Input choice:** replace only `racket_target.target_code` in the selected base solution with the exact canonical `program_solution`; leave `raw_code` untouched.

**Rationale:** the active selected authority should be textually bound to canonical rule hash `c507f6de75fe`. The archival implementation remains useful provenance and is execution-equivalent on all canonical pairs.

**Alternatives considered:**

- Edit canonical `puzzles.jsonl`. Rejected because the canonical rule already passed and did not need a semantic change.
- Delete or overwrite `raw_code`. Rejected because it is archival evidence, not the selected source.
- Accept text divergence because outputs match. Rejected because it leaves the source-of-truth ambiguity the authority gate was designed to expose.

**Probe:** authority sync reports selected exact hash `aedef28e…` in one group and execution parity for both sources.

## D9 — Add portable regressions and independent probes

**Input choice:** 81 task tests under the selected generator, plus `workspace/reference_probe.py` and `workspace/check_authority_sync.py`.

**Rationale:** the root suite does not automatically discover selected task tests, and a test that merely reuses the generator's own mirror would not be independent. The probe reimplements geometry, checks canonical pairs/distribution, and optionally runs real Racket through the packet wrapper.

**TDD record:** the initial focused suite failed 71 tests and passed 9 against the baseline. After the implementation it passed 80; an additional AST regression then failed on nonliteral AXES metadata before the final literal fix, after which 81 passed.

**Failure retained:** the first direct probe invocation lacked the wrapper-provided Racket runtime (`checks/bdcb4c9eb6bd_reference_probe.log`). The wrapper rerun is the valid parity evidence.

## D10 — Stop after source-bound final verification

**Decision:** stop with no remaining source blocker after the exact-path battery, portable task tests, 300-lesson census, independent 400-draw probe, 37-grid Racket parity, both solve records, two adversarial audits, and fresh-delta replay.

**Reason:** additional undeclared rival search may still find hypotheses, but the requested repair is bounded and all required gates are green. Catalog approval and masked-query scoring remain maintainer-owned.

## 2026-10-25 native parametric review `review-5af5df705f6335a0`

Production `generator.py` and canonical rule `c507f6de75fe` remain unchanged. The task-local native family lives in `workspace/parametric/` and has one exact canonical default plus one sequential alternative:

- `finish_rule=project_only` returns the selected canonical Racket program byte-for-byte.
- `finish_rule=project_then_bridge` first performs the canonical fill-and-project transformation, then finds rows or columns whose newly created color-2 projections reach both opposite borders and bridges their remaining background cells with color 3.

### Current decisions

1. **Preserve exact canonical bytes as the default.** The extension is isolated in the task-local promotion adapter; it does not modify the approved production generator or canonical authority.
2. **Require a real Stage-A intermediate.** The raw input contains no color 2, so Stage B cannot select a bridge axis without consuming the completed/projected Stage-A grid. The protected wrong-intermediate witness changes 9 final cells.
3. **Teach the distinction at the minimum two demonstrations.** An early audit found that “bridge any row or column with one projected border contact” fit the first draft’s two demonstrations and failed a later query. The curriculum now includes a safe unpaired projection in each orientation, so this rival is rejected before queries.
4. **Keep queries independent and sequentially private.** The adapter supports 2–6 demonstrations and 1–4 independently generated, prefix-stable queries; the fourth query is a substantive 30×30 case touching all four boundaries. Public views reveal only demonstrations and the current query input.
5. **Treat finite audits as bounded evidence.** The self-audit checks 26 declared rivals over four qualified episodes, but does not claim uniqueness against arbitrary programs.

### Final reviewer evidence

- `checks/bdcb4c9eb6bd-portable-tests/result.json`: 90/90 selected-task tests passed.
- `checks/bdcb4c9eb6bd/qualification/`: two settings × seeds 0 and 17, four jobs, 32 protected-Racket label evaluations.
- `checks/bdcb4c9eb6bd/replay-compare.json`: deterministic replay reproduced the program and execution hashes.
- `checks/bdcb4c9eb6bd/self-audit.json`: four episodes, 26 declared rivals, 52 rival evaluations, zero demonstration survivors.
- `checks/bdcb4c9eb6bd/public-preview/private/manifest.json`: four episodes and 16 sequential public views passed projection checks.
- `checks/bdcb4c9eb6bd/causal/witness.json`: protected wrong-intermediate counterfactual changed 9 cells.

Reviewer status is **ready**. Exact-source owner integration, fresh owner qualification/acceptance replay, and any training-admission decision remain pending; `training_admitted` is false.

Owner reconciliation: Three exact disjoint rules share randomized rectangle scenes: opposed outward rays teach bridging; an unmatched orthogonal ray rejects over-bridging; compact versus thin rectangles separate interior area from perimeter. Supports 2–6 demos, four default queries and 30×30. The first two demos use opposite axes and reversed source order. The original sampler remains available in prototype.py. The exact prior programs and incoming alternate are preserved. Fresh source-bound acceptance and causal evidence: `evidence/owner-variant-reconciliation/current.json`.
