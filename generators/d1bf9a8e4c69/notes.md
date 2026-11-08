# Working notes: d1bf9a8e4c69

## Baseline diagnosis

The imported generator SHA-256 was `ada66b645985e011eef3f969e15029905e2d9bff2a51e4c274ca266bfba0194f`. Its before battery had 7 green, 2 advisory, and 3 failed stages. It omitted `RULE_HASH`, declared axes that were inert or not observable, accepted unknown overrides, and mixed lawful inputs with supposedly degenerate texture modes. The override stage recorded 4,768 findings over 96,300 draws and 1,070 cases. The semantic gate reported no contract. Canonical examples also admitted a strong per-color-bbox shortcut because all objects used distinct colors.

The original source is retained at `workspace/baseline_generator.py`; detailed evidence is under the packet's `checks/before/` directory.

## Repair history

1. Added task-local tests before implementation. The initial run failed 16 tests and passed 1 (`checks/tdd-red.log`).
2. Replaced the false schema with five exact observable axes and rejected unknown keys.
3. Rebuilt the object grammar around L, zigzag, irregular, and mixed connected components, with distinct and repeat-pair palettes.
4. Added a Python rule mirror, canonical-shortcut declaration, semantic witnesses, named lesson competitors, and a two-example lesson-identifiability contract.
5. Added a deterministic four-profile schedule: every adjacent pair includes both a mixed scene and a separated repeated-color pair.
6. Initially anchored 25% of default draws to canonical profiles. A new pinned-census regression failed at 13/60 envelope hits (`checks/tdd-profile-red.log`; `checks/iter-profile/`). Raising the anchor to 50% produced 34/60 hits in the reusable probe and 34/60 in the final repository gate.
7. Added `workspace/distribution_probe.py` test-first. It derives axes and rival declarations from the selected generator rather than maintaining a copied rival list.

Final task-local tests: 19 passed (`checks/task-tests-final.log`). Final generator SHA-256: `458e1558ab9ada63796e1b5ab6a9601f4bd28094c0687140aedf17390105c86b`.

## Current measured distribution

The source-bound probe sampled indices 0–23 in each of easy, medium, and hard, using SHA-256-derived seeds:

- 72/72 unique inputs, no `self_check` failures.
- 77 distinct normalized component shapes.
- Object counts: 52 two-object, 13 three-object, 7 four-object scenes.
- Palette patterns: 36 distinct and 36 repeat-pair scenes.
- Strict canonical-like hits: 12/24 in each band.
- All 12 cyclic two-example windows were identifiable; every named rival was refuted in every window.

See `workspace/distribution_probe.py` and `checks/final_distribution_probe.json`.

## Known limits

The grammar intentionally covers 2–4 objects, grids 8–13 by 9–14, non-touching objects, and non-overlapping output footprints. The semantic contract covers declared competitors, not every conceivable program. The broader repository test run had one unrelated timing-sensitive failure in `tests/test_review_runtime.py::test_streaming_timeout_retains_progress_and_stops_child`; 143 tests passed and 28 Racket-dependent tests were skipped. No Racket authority was edited.
## Current reviewer considerations

Source SHA-256: `458e1558ab9ada63796e1b5ab6a9601f4bd28094c0687140aedf17390105c86b`.

# Design decisions for d1bf9a8e4c69

All selected-source measurements in this document refer to final generator SHA-256 `458e1558ab9ada63796e1b5ab6a9601f4bd28094c0687140aedf17390105c86b` unless a before/intermediate source is named.

## D1 — Replace the false public schema instead of patching labels

**Decision.** Expose only five axes that `generate()` can honor exactly and `observe_overrides()` can recover: `grid_h` (8–13), `grid_w` (9–14), `object_count` (2–4), `shape_family` (`l_shape|zigzag|irregular|mixed`), and `palette_pattern` (`distinct|repeat_pair`). Reject unknown keys.

**Rationale.** The imported schema claimed dimensions and palette/object controls that were not honored together, plus one-token axes that could not be probed. The before override run found 4,768 findings in 96,300 draws, including 3,510 mismatches and 870 generation errors ([G2 evidence](checks/before/checks/d1bf9a8e4c69_before_override.log)). A smaller truthful schema is more useful than a larger nominal one.

**Rejected alternative.** Keep `n_blobs`, `palette_size`, `n_distinct_colors`, `palette_kind`, `position_bias`, `density`, and texture declarations, then special-case each incompatibility. This would preserve duplicated/ambiguous controls and require a large incompatibility matrix without adding meaningful training variation.

**Failure modes/limits.** The new ranges are deliberately finite; callers cannot request arbitrary grid sizes or object counts. Verification: 17,460/17,460 accepted draws across 194 override cases, unknown keys rejected ([final override](checks/after/checks/d1bf9a8e4c69_after_override.log)).

## D2 — Use an explicit connected-shape grammar

**Decision.** Generate two to four 4-connected components from L-shape, zigzag, and irregular families, with rotations/reflections and additional irregular growth. Require every component to span at least 2×2, contain a non-corner cell that must be erased, and omit at least one bbox corner that must be added.

**Rationale.** Those constraints make both directions of the transformation observable: deletion of interior/non-corner source cells and insertion of absent corners. Multiple families prevent the rule from collapsing into an L-template transform.

**Rejected alternative.** Retain only random-walk blobs. They were diverse geometrically, but the old generator had no stable family labels or lesson policy and did not deliberately cover shape-template rivals.

**Failure modes/limits.** Generated components are orthogonally separated and their output footprints do not overlap. This avoids ambiguous color collisions but excludes some lawful inputs on which the Racket rule itself remains defined. The final source-bound census found 77 unique normalized component shapes over 72 draws ([probe](checks/final_distribution_probe.json)).

## D3 — Add separated same-color objects as a first-class palette pattern

**Decision.** `palette_pattern=repeat_pair` gives exactly one pair of disconnected components the same color; `distinct` keeps all component colors different.

**Rationale.** All three canonical pairs use distinct component colors, so the strongest simple rival is “merge all cells of each color and paint one global bbox per color.” It fits 3/3 canonicals. A separated repeated-color pair creates an exact disagreement while preserving the intended component rule ([G1 counterexample](checks/generator_shortcut_counterexample.json)).

**Rejected alternative.** Make every scene repeated-color. That would overfit the curriculum to one ambiguity and reduce resemblance to canonical examples. The default schedule instead balances 36 distinct and 36 repeat-pair scenes in the 72-draw probe.

**Failure modes/limits.** The palette grammar allows one repeated pair, not arbitrary multiplicities. This is sufficient for the known canonical shortcut but not exhaustive color-reuse coverage.

## D4 — Make the lesson, not an isolated draw, the unit of teaching

**Decision.** Set `EXAMPLES_NEEDED = 2` and use a four-profile cyclic schedule:

1. mixed L/zigzag, distinct colors;
2. L shapes, repeated pair;
3. mixed zigzag/irregular, distinct colors;
4. irregular shapes, repeated pair.

Every consecutive pair therefore contains a mixed-family scene and a repeated-color scene.

**Rationale.** Witness frequency in a pool does not guarantee that each assembled lesson contains the needed evidence. The cyclic schedule makes the guarantee local to every lesson start.

**Rejected alternatives.** A one-example lesson cannot simultaneously guarantee both broad shape evidence and the repeated-color counterexample without making every single scene maximally busy. Pure random scheduling can produce unlucky all-distinct or single-family lessons even when pooled frequencies look good.

**Failure modes/limits.** Deterministic scheduling introduces periodicity of four. Geometry, colors, dimensions, placements, and shape variants remain seeded. All 12 windows covering four cyclic starts in each band were identifiable, and all six named competitors were refuted in every window ([probe](checks/final_distribution_probe.json)).

## D5 — Anchor half of default draws to canonical-scale profiles

**Decision.** On a deterministic one-in-two schedule, use one of the three canonical `(height, width, object_count)` profiles: `(8,9,2)`, `(8,10,2)`, or `(9,11,2)`. Other draws use the broader band-dependent ranges.

**Rationale.** The imported source had 17/60 envelope hits but zero support in hard. My first repair used a 25% anchor; a newly written pinned-census test failed at 13/60, below the repository floor of 15 ([G3 red test](checks/tdd-profile-red.log)). The 50% anchor passed with 34/60 in the reusable probe and final gate.

**Rejected alternative.** Keep the 25% anchor because every band had nonzero support. The repository contract measures pooled support as well; 13/60 was objectively insufficient. Anchoring every draw was also rejected because it would eliminate meaningful dimension/object-count breadth.

**Failure modes/limits.** The exact 50% rate is empirical rather than theoretically optimal. Final pinned census: easy 12/20, medium 10/20, hard 12/20 envelope hits ([probe](checks/final_distribution_probe.json)).

## D6 — Declare executable semantic rivals and witnesses

**Decision.** Add `rule_mirror`, `CANONICAL_SHORTCUTS`, `SEMANTIC_WITNESSES`, `LESSON_COMPETITORS`, `strict_canonical_like`, and `lesson_identifiable`. Named competitors are identity, keep-existing-corners, bbox-outline, solid-bbox, L-shapes-only, and per-color-bbox.

**Rationale.** The before semantic stage reported `NO_CONTRACT`. Executable rivals turn “this seems teachable” into testable claims and let the gate confirm that every canonical-shortcut declaration really fits canonical pairs before requiring generated counterexamples.

**Rejected alternative.** Only add prose invariants. Prose cannot be run against all lesson windows and tends to drift from the source.

**Failure modes/limits.** Named-rival coverage is not an exhaustive search over programs. The final semantic gate verified 7/7 witness types and 7/7 rival claims over 600 draws, with 12/12 lessons identifiable ([log](checks/after/checks/d1bf9a8e4c69_after_semantic_gate.log)).

## D7 — Remove texture taxonomy rather than relabel broken modes

**Decision.** Declare no helpful, degenerate, or lawful-degenerate textures.

**Rationale.** The old helpful modes were byte-identical to untextured draws, while `line_blobs` and `solid_rects` were labeled degenerate but passed `self_check` ([G2 defect lint](checks/before/checks/d1bf9a8e4c69_before_defect_lint.log)). Neither concept was necessary to express the actual transformation.

**Rejected alternative.** Mark the old degenerates lawful and retain the dead helpful modes for compatibility. That would make the linter quiet without making the generator contract more truthful.

**Failure modes/limits.** There is no texture-axis curriculum. Variation comes from component family, size, orientation, placement, count, palette reuse, and grid profile.

## D8 — Build a source-bound reusable distribution probe

**Decision.** Add [`workspace/distribution_probe.py`](repo/generators/d1bf9a8e4c69/workspace/distribution_probe.py). It imports the selected generator, uses its actual axis/rival/schedule declarations, checks canonical-shortcut fit, searches generated counterexamples, enumerates cyclic lesson starts, and mirrors the pinned profile census.

**Rationale.** Future agents need one command that detects drift among source declarations, distribution, semantic rivals, and profile support. The test for the tool was observed failing while it was absent, then passing after implementation ([red](checks/tdd-probe-red.log), [green](checks/tdd-probe-green.log)).

**Rejected alternative.** A one-off analysis script with copied rival names. Copied declarations can remain green after the generator's real contract changes.

**Failure modes/limits.** The default census is deterministic and finite. It is a regression probe, not a proof over all seeds.

## D9 — Preserve the Racket authority

**Decision.** Do not change the Racket rule or canonical examples.

**Rationale.** The canonical transformation was correct; the defects were in Python generation and teaching evidence. The Python mirror matched the exact Racket output on the retained shortcut counterexample, and final authority sync reports execution parity ([G1 evidence](checks/generator_shortcut_counterexample.json), [authority log](checks/after/checks/d1bf9a8e4c69_after_authority_sync.log)).

**Rejected alternative.** Rewrite the Racket authority merely to align source text with the new Python structure. That would add risk without changing semantics.

## 2026-10-24 native parametric admission handoff `review-b50ba6563a4bd04d`

**Selected design.** Added a task-local native family with `finish=corners_only` and `finish=nearest_corner_bridge`. The default copies the canonical Racket program byte-for-byte. The alternative first materializes each component's bounding-box corners, then selects the unique nearest cross-component corner pair and paints a deterministic row-then-column color-4 bridge through zero cells.

**Why this design.** It preserves the exact existing rule while adding a meaningful, input-dependent A→intermediate→B composition rather than a cosmetic toggle. Inputs are matched across settings, sampling is prefix-stable for 2–6 demonstrations, and four distinct query profiles include a 30×30 case.

**Alternatives rejected.** A bridge chosen directly from original occupied cells was rejected because it bypasses the corner intermediate; it is retained as the causal ablation. Column-first routing, first-two-component selection, same-color component merging, and farthest-pair selection are retained as executable finite rivals rather than admitted settings.

**Evidence.** Twenty-two parametric regressions and 41 staged task tests passed. Protected Racket matched all seven rule programs to their Python mirrors on 20 inputs (140 evaluations). The reusable self-audit covered both settings, seeds 0/17, and every 2–6 demonstration count with zero surviving-rival or parity findings. Native qualification passed both settings at seeds 0/17 with four queries. The retained 30×30 witness changes 21 cells when bridge endpoints are selected from original cells instead of Step-A corners.

**Limits and next action.** Evidence is finite over the declared grammar and rivals; no measured learning gain or universal uniqueness is claimed. Production `generator.py` and the canonical authority remain unchanged. Owner exact-source review, fresh native acceptance replay, and any training admission remain pending.
