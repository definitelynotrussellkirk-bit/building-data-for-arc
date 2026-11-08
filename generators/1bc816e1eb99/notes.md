# Working notes: 1bc816e1eb99

## Review repair

The imported 2.0.1 generator emitted only fixed 2×3 solids and 3×3 one-hole frames, declared controls it did not faithfully expose, accepted unknown overrides, and used a permissive validator. That distribution made the true hole-count rule unnecessarily confounded with component size, fullness, area, and fixed morphology.

Version 3.0.0 replaces the advertised contract rather than retaining dead controls. It pins the selected rule hash, exposes only three reconstructible integer axes, preserves the public input palette, covers all five public inputs under `strict_canonical_like`, and rejects malformed or out-of-domain structural impostors.

## Linked curriculum

The schedule cycles through four profiles. Any consecutive four examples contain a canonical scene plus targeted counterexamples for size, bounding-box fullness, and area shortcuts. `lesson_identifiable` checks declared competitors across the complete demonstration window rather than scoring isolated examples only.

## Authority

The selected base-task Racket text was normalized by removing one comment so it exactly matches the canonical/raw authority text. Executable behavior did not change. Generated outputs continue to come from the selected Racket program; `rule_mirror` exists only for independent probes and regression tests.

## Local review tools

- `workspace/reference_probe.py`: independent component/hole oracle plus batched Racket replay.
- `workspace/curriculum_probe.py`: source-bound, deterministic audit of linked lessons per difficulty band, all cyclic starts, named rival survival, uniqueness, validation, and sampled Racket parity.
- `workspace/scalar_boundary_probe.py`: portable source-bound audit of `generate` and `schedule_profile`; it creates its output directory, records malformed/valid scalar dispositions, checks valid-call determinism, and exits nonzero on contract drift.
- `tests/test_generator.py`: focused contract, canonical-coverage, override, curriculum, shortcut, determinism, and adversarial-validator regressions.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `ef86b752494b893b953a714ac139f715ae6521c07471f82f316ff0fb8f914f3f`.

# Decisions for 1bc816e1eb99

## D1 — Treat the selected Racket program as the sole authority

**Original rationale:** unknown; the imported generator had no `RULE_HASH`, while the selected `target_code` differed from canonical/raw text only by one comment.
**Decision:** pin `RULE_HASH = "0c3f64fb33c3"`, keep generated outputs owned by Racket, and remove the comment-only selected-source divergence.
**Alternatives rejected:** rewriting the Racket rule, or treating the Python mirror as authority. Neither was justified because all authorities already had execution parity on all five canonical pairs.
**Probe:** rule smoke and authority sync in `checks/after/`.
**Failure mode/limit:** exact-source normalization is intentionally narrow; no semantic rule change was made.

## D2 — Preserve the canonical input palette

**Original rationale:** the old generator optionally added a magenta distractor, although the public task uses only 0 and 4.
**Decision:** generate only background 0 and yellow 4 inputs.
**Alternatives rejected:** arbitrary distractor colors or recoloring source components; both add a second filtering task not evidenced by the canonical examples.
**Probe:** `self_check`, canonical coverage tests, and profile-floor census.
**Failure mode/limit:** this does not teach color invariance; it deliberately teaches the selected canonical task.

## D3 — Advertise only exact, reconstructible controls

**Original rationale:** the baseline exposed broad generic axes and textures that were dead, overlapping, or not observable.
**Decision:** retain only `grid_h` (11–15), `grid_w` (12–18), and `n_components` (2–4), with strict type/range checking and `observe_overrides`.
**Alternatives rejected:** keeping compatibility aliases or accepting unknown keys. Silent aliases make override evidence ambiguous.
**Probe:** boundary and invalid-override tests plus `checks/after/checks/1bc816e1eb99_after_override_results.json`.
**Failure mode/limit:** shape family is curriculum-controlled rather than user-overridable.

## D4 — Use a linked period-four curriculum

**Original rationale:** independent random examples can be valid while a wrong rule survives the complete demonstration set.
**Decision:** cycle `canonical`, `small_frame_large_solid`, `concave_zero_hole`, and `same_area_opposite_topology`; require four demonstrations. Every four-example window contains all profiles, including across wraparound.
**Alternatives rejected:** pooled witness quotas and purely random profile selection. Neither guarantees a complete lesson.
**Probe:** all four cyclic starts in tests and 32 repetitions of each start per band in `checks/curriculum-probe-final.json`.
**Failure mode/limit:** the schedule is deliberately regular; a consumer should shuffle lessons, not examples within a lesson.

## D5 — Target the three strongest canonical-fitting visual shortcuts

**Original rationale:** public examples permit size/bounding-box, non-fullness, and area threshold explanations in addition to hole counting.
**Decision:** include a small frame with a large solid, a one-edge notch with zero holes, and equal-area components with opposite topology. Declare executable rivals and witness-to-rival claims.
**Alternatives rejected:** descriptive-only witness names or hand-written claims without executable outputs.
**Probe:** canonical shortcut fit test, semantic gate, and source-bound rival-survival probe.
**Failure mode/limit:** a “perfect rectangular frame means cyan” proxy remains possible because generated one-hole shapes are still rectangular frames; this is explicitly reported rather than hidden.

## D6 — Keep component geometry supported and auditable

**Original rationale:** allowing arbitrary blobs would improve variety but make validator and topology edge cases harder to distinguish from generator bugs.
**Decision:** support filled rectangles, rectangular frames, and one exact 3×3 perimeter-notch solid; cap component bounding boxes at 5×5.
**Alternatives rejected:** unrestricted random walks and multi-hole shapes. They broaden the task beyond the selected zero-versus-one-hole rule envelope.
**Probe:** adversarial validator tests and independent `workspace/reference_probe.py`.
**Failure mode/limit:** morphology is narrower than the mathematical rule and should not be described as universal.

## D7 — Place components in separated slots but exercise borders

**Original rationale:** component merging would change the object partition seen by the rule.
**Decision:** use four slots separated by a full row/column, with deterministic random placement and a sampled forced border contact.
**Alternatives rejected:** unconstrained rejection sampling, which is slower and can silently bias counts.
**Probe:** 128 draws per band in task tests; at least 20 border-contact scenes and at least 50 scenes containing both branches are required.
**Failure mode/limit:** near-touching/touching components are outside the generated domain.

## D8 — Make validation structural, not cosmetic

**Original rationale:** the baseline validator mostly checked dimensions/header-like facts and accepted impostors.
**Decision:** validate rectangular ARC grids, dimensions, palette, 2–4 four-connected components, supported shape class, and zero/one hole count. `strict_canonical_like` separately defines the public-profile subset.
**Alternatives rejected:** one permissive validator for both domain validity and canonical similarity.
**Probe:** malformed, foreign-color, one-component, unsupported-shape, and two-hole fixtures.
**Failure mode/limit:** exact known shape support is conservative and may reject lawful authority inputs outside the declared generator domain.

## D9 — Build independent, reusable review tooling

**Original rationale:** testing generator helpers against themselves can reproduce the same bug on both sides.
**Decision:** put independent component/hole analysis and Racket batching in `workspace/reference_probe.py`, and a source-bound linked curriculum audit in `workspace/curriculum_probe.py`.
**Alternatives rejected:** copying the generator’s private helpers or hard-coding competitor names in the probe.
**Probe:** `checks/curriculum-probe-final.json` records source hashes, sampler policy, domain limits, unique counts, declared rivals, and 64 Racket comparisons.
**Failure mode/limit:** 128 deterministic lessons per band are strong finite evidence, not a proof over all seeds.


## D10 — Fail closed on malformed public scalars

**Original rationale:** the retained audit showed that `GenCtx` and `int(sample_index)` silently coerced booleans, floats, strings, and negative indices at the two public entry points.
**Decision:** require literal Python integers for `seed` and `sample_index`, reject negative `sample_index`, and run the shared validation before schedule arithmetic or `GenCtx` construction in both `generate` and `schedule_profile`. Preserve generator version `3.0.0` because every valid integer call keeps the existing deterministic stream.
**Alternatives rejected:** relying on an outer caller to sanitize values, coercing with `int`, or validating only `generate`. Each leaves one directly callable public boundary ambiguous or maps malformed requests onto valid examples.
**Probe:** the archived source accepted all 14 malformed entry-point cases; the repaired source rejected all 14 while accepting and deterministically replaying all 6 valid controls. Focused task tests passed 41 tests, and the curriculum probe retained 300/300 identifiable lessons with 32/32 sampled Racket matches.
**Failure mode/limit:** the packet's native `defect_lint` launcher could not start because it resolves `shared/scripts/generator_battery_subject.py` although the helper is under `shared/tools/`. The repair therefore uses the direct source-bound scalar probe, focused tests, and curriculum/Racket probe; it does not claim a passing native defect-lint stage.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-fffdbfa1bae9eb75:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `61a5d69dd325c6d0580ea40a31baac0a5e463b53b6bd382f6f9190a145dc9d7e`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted source ef86b752494b893b953a714ac139f715ae6521c07471f82f316ff0fb8f914f3f adds exact integer guards at generate and schedule_profile. Reviewer retains before14invalid accepted / after14rejected and6valid deterministic controls, 41focused tests and32Racket matches. Native defect-lint helper failed before execution and is not claimed passed.

### Assessment or prior finding

## 1bc816e1eb99

**Reproduced boundary finding (A2).** Current generator SHA-256:
`61a5d69dd325c6d0580ea40a31baac0a5e463b53b6bd382f6f9190a145dc9d7e`.
Lint passes and selected tests pass **33/33**, but `defect_lint` reports **33**
`strict-scalar` findings. A direct current-source probe confirms that all seven
representative invalid calls were accepted and produced self-check-clean grids:
boolean/float/string seeds, boolean/float/string sample indices, and
`sample_index=-1`.

The probe records every argument type, output shape, and output hash in
`checks/audit/1bc816e1eb99/strict_scalar.json`; its reusable script is retained as
`strict_scalar_probe.py`. This is a public-boundary contract defect even though
the produced grids happen to be lawful and the target is catalog-approved.

Evidence:

- `checks/audit/1bc816e1eb99-lint/result.json` (pass);
- `checks/audit/1bc816e1eb99-task_tests/result.json` (33/33 pass);
- `checks/audit/1bc816e1eb99-defect_lint/result.json` (33 findings);
- `checks/audit/1bc816e1eb99/strict_scalar.json` (direct reproduction).

I inspected the target's existing executable semantic rivals and selected tests
but did not establish a second independent semantic counterexample. That is not
a clean-audit claim; the scalar defect above is concrete and source-bound.

**Patch status.** Audit-only target; no files under this generator were modified.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-fffdbfa1bae9eb75-v0001/audit_assets.json), manifest SHA-256 `53da6a8774a5cc8d018d60362b099c49368815ce64c70c3c8ec1ddba0349fe14`.
<!-- arcpuzzles-current-audit-assessment:end -->
