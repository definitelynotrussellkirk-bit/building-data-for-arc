# Working notes: efdd2b265cc8

## 2026-10-07 review

- Pinned the retained Racket rule with `RULE_HASH = f5d00e3992ee`; no rule edit.
- Replaced the drifting rectangular/random-shape sampler with a square,
  four-profile curriculum matching the canonical task scale and morphology.
- Reduced the public intervention surface to two exact axes: `grid_size` and
  `n_colors`. All 36 Cartesian combinations across four difficulty bands are
  constructible.
- Added `self_check`, canonical acceptance, exact override observation, D4
  semantic rivals and witnesses, finite lesson identifiability, and deterministic
  replay/freshness/RNG-purity tests.
- Added `workspace/review_probe.py` so later reviewers can replay canonical,
  exact-axis, semantic-collision, and rotated-lesson checks in one command.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `1fc4b39404df27576fd1c684c2c53189d43aa34cac714bce35e06726261ccb14`.

# Decisions for `efdd2b265cc8`

Final generator SHA-256: `1fc4b39404df27576fd1c684c2c53189d43aa34cac714bce35e06726261ccb14`
Canonical Racket rule hash: `f5d00e3992ee`

## D1 — Preserve the Racket rule

**Choice.** Leave the canonical Racket rule and canonical examples unchanged.

**Original rationale.** The baseline rule already executed correctly: the before rule-smoke stage applied it to 120/120 generated inputs without crash or identity outputs. The defects were in the curriculum contract and distribution, not label authority.

**Alternatives considered.** Rewriting or wrapping the rule to accommodate rectangular examples; modifying canonical examples to endorse version-2 shape variation.

**Probe/evidence.** `checks/before/checks/efdd2b265cc8_before_rule_smoke.json` and the final 120/120 Racket/Python parity report in `checks/after/checks/efdd2b265cc8_after_rule_smoke.json`.

**Failure modes and limits.** A correct rule can still label poor or ambiguous lessons. This decision therefore required separate distribution, semantic, and lesson-level gates.

## D2 — Reverse version 2’s mixed square/rectangular sampling

**Prior choice.** Version 2 sampled both square and rectangular canvases and advertised multiple shape/texture controls. Its likely rationale was broader visual diversity; no authoritative design note established that rectangular output-shape changes were intended.

**New choice.** Generate only square canvases with side length 4–6.

**Reason.** Every canonical input/output pair is square and same-shaped. Baseline defect lint found 44/60 generated pairs with a reshape relation absent from canonical data. Square examples keep the concept focused on coordinate exchange rather than teaching an incidental dimension swap.

**Alternatives considered.** Keep rectangles but balance orientations; include rectangles only at hard difficulty; permit arbitrary 3–12 squares.

**Probe/evidence.** `checks/before/checks/efdd2b265cc8_before_defect_lint.log`; final profile floor and distribution reports under `checks/after/checks/`.

**Failure modes and limits.** The final curriculum does not train rectangular transposition even though the mathematical operation generalizes. That is a deliberate canonical-envelope restriction, not a universal claim about transpose.

## D3 — Use four canonical morphology profiles

**Choice.** Cycle through `four_points_5`, `two_triads_6`, `three_points_4`, and `blob_plus_point_5`.

**Rationale.** These profiles cover the canonical component-count, component-size, palette, and canvas patterns without copying exact canonical coordinates. They provide both singleton and connected-object examples and avoid dense or symmetric inputs that make the transform inert.

**Alternatives considered.** Fully random sparse cells; a single four-point template; unrestricted polyominoes; retaining version-2 negative textures in ordinary generation.

**Probe/evidence.** The semantic gate observed all four profiles across 600 draws, with counts 147, 133, 170, and 150 respectively. Profile floor accepted all four canonical inputs and hit exact profiles in 60/60 draws.

**Failure modes and limits.** Four profiles are not exhaustive morphology. Deterministic cycling can expose schedule period four to downstream consumers, so lesson identifiability is checked at every cyclic start in the reusable probe rather than assumed from frequency.

## D4 — Expose only two exact controls

**Choice.** Declare `grid_size=4..6` and `n_colors=2..4`; remove inert texture, position-bias, and loosely defined shape controls.

**Rationale.** A small exact API is more useful than a broad dishonest one. Both retained axes can be observed directly from the generated grid, and every Cartesian combination is constructible in every difficulty value.

**Alternatives considered.** Keep old axes as diagnostic metadata; declare many incompatibilities; retain textures but implement them later.

**Probe/evidence.** Official override gate: 1,440/1,440 accepted draws over 16 cases, zero findings, unknown key rejected. Task tests enumerate all 4 bands × 3 sizes × 3 color counts. `workspace/review_probe.py` repeats that matrix with three seeds per case.

**Failure modes and limits.** The two axes do not directly control morphology; profile selection remains scheduled. A future morphology override should be added only with an observer and full joint-composability tests.

## D5 — Require each input to distinguish transpose from all other D4 transforms

**Choice.** Reject any candidate where transpose is visually inert or equals identity, clockwise/counterclockwise/180° rotation, horizontal/vertical reflection, or anti-transpose.

**Rationale.** This is stronger and cheaper than merely hoping a full lesson contains a disambiguating example. It prevents symmetric examples from consuming demonstration slots without semantic value.

**Alternatives considered.** Allow ambiguous individual examples and enforce only lesson-level disambiguation; check identity only; infer rivals from canonical pairs without declaring them.

**Probe/evidence.** Seven declared competitors, seven transformation witnesses, and zero collisions across 600 semantic draws, 108 exact-axis probe draws, and the 300-lesson census.

**Failure modes and limits.** D4 is a finite, task-relevant rival family, not the space of all hypotheses. Some harmless symmetric examples could be valid when paired with strong demonstrations; this policy intentionally trades that diversity for teaching density.

## D6 — Three demonstrations, one query, arbitrary query position

**Choice.** Set `EXAMPLES_NEEDED=3`; assemble four consecutive scheduled examples, use three as demonstrations, and permit any of the four positions to be held out as query.

**Rationale.** Three demonstrations are ample because each accepted example already refutes all seven declared rivals. Query rotation removes accidental reliance on “the last profile is always the test.”

**Alternatives considered.** Two demonstrations; fixed query-last ordering only; four or more demonstrations.

**Probe/evidence.** The final semantic smoke test passed 12/12 lessons and 48/48 rotations. The larger source-bound census passed 300 production lessons and all 1,200 rotations. The reusable probe checks 64 starts per band value and every query position, for 1,024 query checks.

**Failure modes and limits.** These checks reuse a finite declared rival set and finite starts. Downstream assemblers that alter demonstrations, colors, or labels need their own source-bound check.

## D7 — Deterministic schedule plus bounded constructive rejection

**Choice.** Use the local generation context and a deterministic profile schedule; build candidates, then accept only those passing `self_check` and D4 uniqueness.

**Rationale.** Determinism, fresh outputs, and no global RNG mutation make failures replayable. Rejection is bounded because the small grid/profile space has abundant valid placements.

**Alternatives considered.** Global `random`; fixed literal templates; unbounded rejection; post-hoc repair of invalid grids.

**Probe/evidence.** Focused tests cover deterministic replay, fresh object identity, global RNG preservation, invalid arguments, and schedule coverage. The official battery reported no generation crash across its sampling.

**Failure modes and limits.** Rejection-based construction can become fragile if future constraints are added without measuring acceptance. New constraints should add a worst-case exact-axis test before changing production code.

## D8 — Keep Python mirrors diagnostic and add a reusable replay probe

**Choice.** Retain `rule_mirror` for tests and diagnostics, while treating Racket as sole label authority. Add `workspace/review_probe.py` for canonical, exact-axis, replay, and lesson checks.

**Rationale.** Python gives cheap local feedback; source-bound Racket checks prevent a matching Python bug from certifying itself. Future agents can replay the most valuable invariants with one command.

**Alternatives considered.** Remove the mirror entirely; use only the full battery; duplicate a hard-coded rival list in the probe.

**Probe/evidence.** `checks/review-probe.json` is green at the final source hash. The probe reads `AXES` and `LESSON_COMPETITORS` from the actual generator rather than copying them.

**Failure modes and limits.** The probe cannot certify undeclared hypotheses or Racket parity by itself. Acceptance still requires the Racket-backed battery and source-bound lesson evidence.
