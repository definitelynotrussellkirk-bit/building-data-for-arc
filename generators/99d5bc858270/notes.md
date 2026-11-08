# Working notes: 99d5bc858270

## 2026-10-03 review — version 3.1.1

Baseline generator SHA-256: `74ab1e01b24b99eb821dee1e4ddccd3aab5a83f619f2c96f97ea7701ea4e99e8`.
Final generator SHA-256: `3dc7718bd44600c5b7d8fbb9cd1447b17e1548a130747e70ec199b37ac8999c0`.
Selected canonical rule hash: `e48cc46570d0` (unchanged).

The lead came from retained return `review-9590ce90455a4905:v0001`, whose audit matched the pinned baseline source hash. I independently reproduced its two material findings: the old validator rejected all three canonical inputs, and the old sampler excluded separated casters sharing a ray projection, leaving a plausible farthest-caster shortcut unchallenged.

The repair replaced the narrow sampler with a constructive full-domain sampler. It supports all four edges and four corners, follows the selected rule's horizontal corner priority, honors all exact advertised overrides in every band, rejects unknown/ill-typed controls, pins `RULE_HASH`, and emits a protected shared-projection gap in every scene. Three witness morphologies and variable separations prevent one fixed U-shape from becoming a new cue. Decorations use one or two caster colors but cannot fill the protected gap.

Canonical 6×9 dimensions are weighted rather than made exclusive. Version 3.1.0 used an anchor multiplicity of 20 and passed 11/12 gates, but its deterministic profile sample reached only 13/60 (21.7%), below the 25% warning floor. Version 3.1.1 changes only that default weight to 36; the final profile check reached 24/60 (40%), with support in all bands.

Task-local tests are in `tests/test_generator.py`; reusable independent geometry and real-Racket probes are in `workspace/reference_probe.py`. Final evidence: 12/12 battery stages green, 59/59 task tests, 300/300 lesson windows materialized with 900/900 unique inputs and zero ambiguity, and a post-repair visible-only solve passed 3/3 examples on revision 1.

Known limit: the semantic contract tests a finite named rival family. It establishes that generated lessons refute the demonstrated farthest-caster shortcut, not that every possible learner shortcut is excluded.
## Current reviewer considerations

Source SHA-256: `3dc7718bd44600c5b7d8fbb9cd1447b17e1548a130747e70ec199b37ac8999c0`.

# Decisions — 99d5bc858270

Final generator: version `3.1.1`, SHA-256 `3dc7718bd44600c5b7d8fbb9cd1447b17e1548a130747e70ec199b37ac8999c0`.
Selected Racket authority: `e48cc46570d0`; unchanged.

## D1 — Keep the selected Racket rule and repair only the input side

The selected canonical rule solves every canonical pair and the final authority check reports selected-source synchronization plus execution parity. The defect was in Python validation/sampling, not labeling, so I pinned `RULE_HASH` and made no Racket edit. A rule rewrite would add authority risk without fixing lesson coverage.

Evidence: `checks/after/checks/99d5bc858270_after_authority_sync.json`.

## D2 — Admit the full canonical border-light domain

The old validator treated corners as ambiguous despite canonical corner examples. The repaired domain accepts top, right, bottom, left, and all four corners. At corners it implements the authority's observed precedence: left/right membership determines horizontal casting before top/bottom membership is considered.

Rejected alternative: declare corners out of domain. That would preserve a known contradiction with the canonical task and leave the validator unable to accept all three canonical inputs.

Probe/test: `test_accepts_every_canonical_input_and_oracle_matches` and `test_default_curriculum_covers_canonical_scale_corners_and_all_directions` in `repo/generators/99d5bc858270/tests/test_generator.py`.

## D3 — Expose only three exact, meaningful controls

The final axes are `grid_h`, `grid_w`, and `light_position`. Every exact value in the documented range is legal in every difficulty band. Unknown keys, booleans/floats, and out-of-range values fail explicitly; no advertised axis is silently ignored.

Rejected alternative: retain broad decorative axes from the imported generator. They did not correspond to independently observable exact controls and made override testing misleading.

Measured result: 26,190/26,190 override draws accepted as expected across 291 cases per band; unknown keys were rejected. Evidence: `checks/after/checks/99d5bc858270_after_override_results.json`.

## D4 — Weight canonical scale without collapsing the domain

All bands retain heights 6–15 and widths 7–16. Defaults add difficulty preferences and a repeated 6×9 canonical anchor. Version 3.1.0 used 20 anchor copies; the completed aggregate preserved at `checks/after-attempt1-profile-floor/` passed 11/12 stages but measured only 13/60 canonical-profile hits (21.7%). Version 3.1.1 raises the anchor multiplicity to 36 and reached 24/60 (40%): easy 6/20, medium 10/20, hard 8/20.

Rejected alternatives:

- force all outputs to 6×9, which would eliminate useful scale variation;
- exempt hard mode from canonical support, which would violate the profile-floor contract;
- tune to one observed random seed without retaining the deterministic failed aggregate.

Final evidence: `checks/after/checks/99d5bc858270_after_profile_floor.json`.

## D5 — Construct a lesson-level counterexample to the known shortcut

The old sampler avoided multiple separated casters on one projected ray. A learner could therefore keep only one caster per row/column and still fit generated lessons. Every repaired input contains at least one shared projection with a real zero gap, and the generator declares the executable `farthest_caster_per_projection` rival in `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS`.

A random “hope two casters collide” strategy was rejected because witness frequency does not guarantee that each assembled lesson refutes the rival. The production sampler instead constructs the witness before optional decoration and protects its gap.

Final semantic gate: 600/600 draws without crashes; strict-canonical-like rate 248/600 (41.3%); 12/12 smoke lessons identifiable. Strong census: 300/300 lessons, 900/900 unique inputs, zero ambiguous lessons, and all three declarations refuted in every lesson. Evidence: `checks/after/checks/99d5bc858270_after_semantic_gate.json` and `checks/lesson-census-final.json`.

## D6 — Vary witness morphology to avoid replacing one shortcut with another

An intermediate implementation always emitted the same 5-cell U witness. A test-first self-review demonstrated that its shared-projection gap length was fixed. The final sampler chooses among open pair, parallel dominoes, and bridge motifs, varies separation from 2 upward when space permits, and allows one or two caster colors plus independent decorations.

Rejected alternative: keep the fixed U because it already defeated the named rival. It would make a local shape template synonymous with the task and reduce training value.

Probe/test: `test_witness_geometry_is_not_a_single_fixed_gap_template` and `shared_projection_gap_lengths` in the task workspace.

## D7 — Use independent and selected-authority tests

The test suite does not derive expected outputs from the generator implementation. It combines an independent geometry oracle, canonical-pair assertions, destructive validator mutations, exact override checks, hash-seed determinism, lesson-window rival checks, and 27 real-Racket parity cases. Both the direct and portable source-bound invocations passed 59/59 on the final bytes.

Evidence: `checks/direct-tests-final/pytest.log` and `checks/task-tests-v311/result.json`.

## Remaining limitations

- Declared-rival coverage is finite; it does not prove universal identifiability.
- Every generated scene contains a shared-projection witness, which is intentional for teaching but overrepresents that relation relative to an unconstrained natural distribution.
- The large lesson census uses consecutive two-demo/one-query windows and does not independently rotate every pair through every role beyond its documented schedule.
- Catalog approval/train-safety remain maintainer decisions; passing checks do not set them.
