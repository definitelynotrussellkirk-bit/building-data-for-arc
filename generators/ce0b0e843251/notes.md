# Working notes: ce0b0e843251

## 2026-09-28 review `review-d95f82861019d7d9`

Canonical analysis found a backbone-plus-local-branch wall grammar, not the prior full-row/full-column divider distribution. Canonical linked signatures are `(9,11,6,3,3)`, `(9,12,7,5,4)`, and `(10,12,8,6,5)` for `(h,w,palette,rooms,seeded)`.

Baseline reproduced:

- missing `RULE_HASH`;
- canonical palette size 8 unreachable;
- `0/60` exact canonical profiles and `5/60` envelope support;
- median modal-background object count 1 versus canonical 4;
- no semantic contract;
- permissive self-check accepted minimal impostors;
- 16,983 override findings, including dead axes and unknown-key acceptance.

Version 3.0.0 rebuild:

- color-7 frame;
- one/two color-5 spanning backbones plus compartment-local branches;
- four profiles with 3–6 rooms;
- exact transpose orientation;
- all seeded or exactly one seedless room;
- globally distinct one-cell seeds;
- strict topology-aware `self_check`;
- `RULE_HASH`, `rule_mirror`, `strict_canonical_like`, `semantic_signature`, and `observe_overrides`;
- focused tests under `tests/`.

An intermediate after battery failed only morphology (`obj_count` median 1). A test reproducing the gate census was added first. Medium seeds now prefer room-interior cells when available, while hard seeds retain edge placement. The aggregate median became 2 and the final battery passed all 12 stages.

Final verification: 22 focused tests pass; the full repository suite passes 132 tests with packet Racket; standalone lint passes; final persistent battery is 12/12 green.
## Current reviewer considerations

Source SHA-256: `a5cb3cce9a4254e79d7f33c8487c8c3aa176ef572cc97d1da86d67ad6a13ea4c`.

# Decisions for `ce0b0e843251`

## 1. Preserve the color-7 outer frame

**Choice.** Every edge cell is 7 and no interior cell may be 7.

**Original rationale.** The old generator and all canonical inputs use 7 as the enclosing wall. The original notes did not explain why color 7 was chosen beyond matching the source task.

**Alternatives considered.** Randomizing the frame color, allowing gaps, or treating 7 as an ordinary seed color.

**Probe.** Canonical inspection plus destructive border mutations in the focused tests and repository self-check battery.

**Failure mode avoided.** A model could otherwise learn generic flood fill without recognizing the frame/wall roles of 7 and 5.

**Limitation.** This fixes a color role that may be incidental to a more abstract connected-component rule, but it is the only role supported by the selected authority.

## 2. Replace full-line walls with backbone-plus-branch topology

**Choice.** Use one or two spanning color-5 backbone walls and one branch in selected strips. A branch spans only its compartment and terminates at a backbone or frame.

**Original rationale.** Version 2.1.0 used one to three full rows or columns because it was a simple way to create multiple connected regions. There was no retained evidence that this matched canonical topology.

**Alternatives considered.** Keep full rows/columns; sample arbitrary maze walls; copy the three canonical layouts exactly; or use recursive guillotine subdivision of unbounded depth.

**Why selected.** It is the smallest grammar that reproduces all observed canonical structures, genuine T-junctions, and 3–6 rooms while remaining easy to validate independently.

**Probe.** Canonical room reconstruction, strict semantic acceptance, wall-grammar validation, exact-profile gate, and tests that remove dividers or introduce stray wall cells.

**Failure modes avoided.** Cross-shaped full-line grids teach a different segmentation prior; arbitrary mazes risk unsupported complexity; exact copying gives poor diversity.

**Limitation.** Only rectangular guillotine compartments are generated.

## 3. Use four explicit room-count profiles

**Choice.** Profiles create 3, 4, 5, or 6 rooms with base shapes `9x11`, `10x11`, `9x12`, and `10x12` before optional transpose.

**Original rationale.** The old generator exposed independent `grid_h`, `grid_w`, and `n_walls` axes. Their advertised ranges did not match what each difficulty actually accepted, and they did not ensure a desired room count.

**Alternatives considered.** Independent dimensions/wall counts; a single canonical profile; all room counts from 2 through 8.

**Why selected.** A profile ties dimensions, strip count, and branch count into a valid, observable structural request. Three profiles reach the canonical linked signatures exactly; the fourth broadens the lesson without inventing a new rule.

**Probe.** `observe_overrides()`, all exact override combinations, and the canonical profile floor.

**Failure modes avoided.** Invalid override combinations, misleading axis metadata, and accidental room-count collapse.

**Limitation.** Dimensions outside the four profile shapes are no longer exposed as public requests.

## 4. Add an exact transpose orientation factor

**Choice.** Generate the vertical-backbone form first; transpose it for `horizontal`.

**Original rationale.** The old generator randomly mixed full horizontal and vertical walls but had no reliable orientation contract.

**Alternatives considered.** Canonical vertical orientation only; independently implement two geometry builders; random rotations/reflections.

**Why selected.** Exact transpose is simple, preserves the rule, produces a recoverable factor, and tests orientation invariance without duplicating geometry logic.

**Probe.** Every profile/coverage combination is tested in both orientations, and validation requires exactly one spanning orientation.

**Failure modes avoided.** Hidden orientation metadata and divergence between separate builders.

**Limitation.** Horizontal layouts are a lawful broadening, not directly observed in the canonical examples.

## 5. Permit either all rooms seeded or exactly one seedless room

**Choice.** `seed_coverage` is `all_seeded` or `one_seedless`.

**Original rationale.** The old generator placed one to three seeds into distinct rooms and allowed any number of remaining rooms to be seedless. Its only semantic requirement was that at least one room fire. Canonical evidence instead shows all rooms seeded in one example and exactly one seedless room in the other two linked profiles.

**Alternatives considered.** Always seed every room; arbitrary numbers of seedless rooms; allow ambiguous multi-seed rooms as ordinary data.

**Why selected.** The factor directly covers the observed contrast that proves seedless rooms remain zero, without flooding the distribution with inactive regions.

**Probe.** Room-wise seed census, exact override tests, canonical signatures, and mirror-vs-input nonidentity checks.

**Failure modes avoided.** A learner that fills every room regardless of seed, or a dataset dominated by uninformative empty rooms.

**Limitation.** Lawful cases with two or more seedless rooms are not sampled.

## 6. Require exactly one seed cell per seeded room and globally distinct seed colors

**Choice.** Each seeded room has one non-{0,5,7} cell; no two rooms share a seed color.

**Original rationale.** Version 2.1.0 had already moved seeds into distinct rooms after earlier collisions caused identity outputs. Global color distinctness was intended but the self-check did not enforce the full contract.

**Alternatives considered.** Repeated colors across rooms; multiple same-color seed cells in one room; ambiguous different-color seeds as ordinary training data.

**Why selected.** It makes the room-to-fill-color relation unambiguous and matches canonical inputs.

**Probe.** Self-check detects multiple seed cells and duplicate colors; destructive tests add a second color to a room.

**Failure modes avoided.** Ambiguous labels, identity outputs, and global-frequency shortcuts caused by repeated room colors.

**Limitation.** The more abstract rule could handle multiple identical seed cells, but canonical evidence does not require that extension.

## 7. Use the full supported seed-color set

**Choice.** Sample from `{1,2,3,4,6,8,9}`.

**Original rationale.** The old generator used the same candidate set, but limited `n_seeds` to 1–3, making canonical palette size 8 unreachable.

**Alternatives considered.** A restricted warm/cool palette; include 0, 5, or 7; color permutations derived from a texture axis.

**Why selected.** The set excludes semantic background/wall colors and supports up to six distinct room seeds plus 0/5/7 roles.

**Probe.** Defect lint canonical-coverage check and distribution palette-range check.

**Failure modes avoided.** Unreachable canonical color cardinality and collisions between seed and wall roles.

**Limitation.** Color 9 is available even though not every canonical row uses it; this is harmless role-preserving broadening.

## 8. Make seed position difficulty-dependent, then calibrate morphology

**Choice.** Easy favors central positions, medium prefers cells not four-neighbor-adjacent to a wall when possible, and hard favors room edges.

**Original rationale.** The old generator chose uniformly random positions and did not document difficulty semantics.

**Alternatives considered.** Uniform placement in all bands; always isolate seeds; always place seeds against walls.

**Why selected.** Position variation prevents a fixed-center shortcut. Retaining hard edge cases matches canonical examples, while medium isolated positions prevent the entire sampled distribution from collapsing into one connected non-background wall object.

**Probe.** The exact 120-draw morphology census used by `generator_distribution_gate.py`; a dedicated regression test watched the old aggregate median fail at 1 and pass at 2 after the change.

**Failure modes avoided.** Center-marker shortcuts and under-fragmented morphology.

**Limitation.** This is a heuristic difficulty distinction, not a measured model-performance calibration.

## 9. Remove cosmetic, contradictory, and degenerate public axes

**Choice.** Expose only layout profile, orientation, and seed coverage.

**Original rationale.** The prior generator advertised `grid_h`, `grid_w`, `palette_kind`, `n_walls`, `n_seeds`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture`. Some were aliases, some were singleton labels, some had ranges inconsistent with difficulty, and degenerate negative fixtures were mixed into the valid texture domain.

**Alternatives considered.** Repair every old axis; mark most as diagnostic; retain negative textures behind a separate API.

**Why selected.** Public controls should correspond to visible, independently testable facts. Negative fixtures are better represented in tests than in the ordinary data domain.

**Probe.** Strict override battery across 29 cases and 2,610 draws; unknown-key rejection; exact factor observation tests.

**Failure modes avoided.** Silent no-op overrides, impossible combinations, typo acceptance, and invalid examples entering normal training.

**Limitation.** Some low-level geometry experimentation now requires code changes rather than an override.

## 10. Strengthen `self_check` from “the rule fires somewhere” to grammar validation

**Choice.** Validate the entire frame, wall grammar, orientation, room count, seed count, seed uniqueness, seedless count, and nonidentity conditions.

**Original rationale.** The old check was designed as a narrow guard against identity outputs after seed collisions. It was not a semantic recognizer.

**Alternatives considered.** Keep a minimal nonidentity check; compare only to a Python rule mirror; validate only canonical dimensions.

**Why selected.** A training generator needs to reject lawful-looking but lesson-destroying inputs before Racket execution. Structural validation is independent of output parity.

**Probe.** Minimal-impostor defect lint, mutation sensitivity, canonical acceptance, and targeted destructive tests.

**Failure modes avoided.** A 5x5 single-room shortcut, stray walls, ambiguous orientation, duplicate seed colors, and scenes with unsupported seedless structure.

**Limitation.** A strict grammar can reject valid abstract variants outside the reviewed distribution; that is intentional until supported by evidence.

## 11. Pin but do not rewrite the canonical rule

**Choice.** Add `RULE_HASH = "ecbd69f623c3"` and an independent Python mirror; leave the Racket source unchanged.

**Original rationale.** No hash pin existed. The Racket rule already produces the correct outputs for all canonical and generated inputs.

**Alternatives considered.** Rewrite the Racket program for style; make the Python mirror authoritative; change the rule to assume rectangular rooms.

**Why selected.** Hash pinning detects authority drift without risking a semantic change. Racket remains the sole label authority.

**Probe.** All canonical pairs, 120 rule-smoke applications, mirror parity, and authority sync.

**Failure modes avoided.** Silent rule drift and accidental dependence on generator-specific Python labels.

**Limitation.** Nonblocking inherited Racket style warnings remain.
