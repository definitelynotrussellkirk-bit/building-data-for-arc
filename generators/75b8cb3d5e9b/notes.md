# Working notes: 75b8cb3d5e9b

## 2026-10-04 review `review-3b145830caae97bf`

The imported 1.3.0 generator used symmetric monochrome motifs. An independent D4 enumeration found 844/2,000 generated inputs (42.2%) where multiple transforms fit source→target and implied different query outputs. Baseline reproducer: seed 1004, sample index 4; all eight transforms fit and yield four query answers.

Version 2.0.0 keeps the canonical Racket authority unchanged and pins `RULE_HASH = 9c9988768752`. Generated source/query supports are full-span 3×3 D4-asymmetric masks with 4..7 occupied cells. All retained axes are exact and pixel-observable. A balanced 112-slot schedule crosses all seven non-identity transforms, both source palette sizes, and eight nuisance morphologies; every exact nuisance tuple appears with every transform.

Retained evidence:

- `workspace/baseline_transform_ambiguity.json`: baseline 2,000-draw census.
- `workspace/final_transform_ambiguity.json`: final 2,000-draw census, zero ambiguity/failures.
- `workspace/transform_ambiguity_probe.py`: independent reusable census tool.
- `tests/test_generator_75b8cb3d5e9b.py`: focused regressions, including the original seed, canonical parity, override honesty, cyclic lesson rotations, exact shortcut declarations, and nuisance-label independence.

Canonical three-cell rows remain accepted, but generation begins at four cells because exhaustive 3×3 support enumeration found no full-span monochrome three-cell motif with a trivial D4 stabilizer.
## Current reviewer considerations

Source SHA-256: `f9d66697f3d1b36e8f1d1c37d124e1ee410361a9d754743fcd74d38304359143`.

# Decisions — 75b8cb3d5e9b

## D1 — Preserve the canonical Racket authority

**Choice.** Leave the Racket rule unchanged and pin `RULE_HASH = "9c9988768752"`.

**Rationale.** The canonical rule correctly implements crop → first matching D4 transform → apply to query. The defect was in generated evidence, not in authority execution. Canonical outputs matched the Python mirror for all three pairs, and final rule smoke matched on 120/120 generated inputs.

**Alternatives considered.** Changing precedence, embedding a transform marker, or rewriting the rule to reject symmetric examples. Each would alter canonical semantics or hide a distribution problem rather than repair it.

**Probe.** Canonical pair regression plus battery `rule_smoke` and `authority_sync`.

**Failure mode/limit.** Individual canonical rows can remain symmetric; their deterministic labels depend on declared precedence. They are accepted as historical canonical evidence, not reproduced by generation.

## D2 — Require one defensible generated query answer

**Choice.** Build source and query motifs from full-span 3×3 supports with trivial D4 stabilizers, then assert exactly one source→target candidate and query orbit size eight.

**Rationale.** The baseline's symmetric L/square-like motifs caused 844/2,000 generated inputs to admit different query labels. Unique source explanation plus a fully discriminative query directly removes that defect.

**Alternatives considered.** Merely rely on Racket precedence; color-code the transform; reject ambiguity only after generation; or add more demonstrations while leaving each row ambiguous. Precedence is invisible, coding trivializes the task, rejection wastes draws, and extra demonstrations do not make a mislabeled single pair suitable for all sampling policies.

**Probe.** `workspace/transform_ambiguity_probe.py` independently reparses pixels and enumerates all eight D4 transforms. It measured 42.2% ambiguity before and 0/2,000 after.

**Failure mode/limit.** The finite census covers generated draws, not arbitrary hand-authored grids.

## D3 — Generate 4–7 occupied cells, while accepting canonical 3-cell rows

**Choice.** Advertise `source_cells` and `query_cells` as exact controls over 4..7.

**Rationale.** Exhaustive enumeration showed no three-cell 3×3 support that spans all rows and columns and has eight distinct D4 orientations. Four cells is the smallest support that can meet the unique-query contract without adding artificial marker colors.

**Alternatives considered.** Two-color three-cell query motifs, hidden incompatibility declarations, or accepting an ambiguous lower boundary. Two-color queries would change the canonical visual abstraction and palette profile; incompatibilities would make the axis misleading; ambiguity is the defect being removed.

**Probe.** Exhaustive mask-bank construction fails loudly if any advertised count lacks a valid support. Boundary override tests exercise 4 and 7 in every band.

**Failure mode/limit.** The generated domain is slightly narrower in cell count than canonical acceptance. This is explicit and does not change the authority.

## D4 — Use one or two source colors and one distinct query color

**Choice.** Preserve source colors under the transform; use a checker-like assignment for two-color sources; keep the query monochrome and color-disjoint from source.

**Rationale.** This maintains the task's transform-only concept, reaches canonical palette sizes, increases object morphology, and prevents color remapping from becoming a second latent operation.

**Alternatives considered.** Arbitrary multicolor queries, recoloring between panels, or a fixed global palette. These respectively complicate the rule, change semantics, or create palette shortcuts.

**Probe.** `observe_overrides`, profile floor, defect lint, and override matrix.

**Failure mode/limit.** Color relationships are deliberately simple; the reasoning challenge is geometric, not palette induction.

## D5 — Replace the first 14-profile design with a balanced 112-slot schedule

**Choice.** Cross seven transforms, both palette sizes, and eight nuisance morphologies so each exact non-relational tuple occurs with every transform.

**Original first-pass rationale.** A 14-profile cycle gave every transform twice, changed transform in adjacent examples, and anchored canonical profiles.

**Rejected after probe.** Most dimension/count tuples still uniquely predicted the transform. The regression `test_nuisance_profile_does_not_reveal_the_transform` failed against that design.

**Final rationale.** The 112-slot design preserves local teaching properties while eliminating the measured profile→label mapping. Six nuisance profiles use canonical 3×3 panels; two wider profiles are never adjacent, so every 14-draw window retains at least seven canonical-size cases.

**Probe.** Full-period grouping by `(panel_h, panel_w, source_cells, query_cells, source_palette_size)`; each bucket must contain all seven transforms. Sliding and cyclic lesson tests cover every query position.

**Failure mode/limit.** A learner could still exploit a more complex pixel statistic not represented by declared axes; finite rival checks do not establish universal shortcut-freedom.

## D6 — Advertise only exact, pixel-observable controls

**Choice.** Keep six axes: panel height/width, transform, source/query cell counts, and source palette size. Reject unknown keys and invalid types/ranges.

**Rationale.** The baseline exposed dead or misleading dimensions. Every retained control now round-trips through `observe_overrides` and is exercised by the exhaustive shared override checker.

**Alternatives considered.** Retain cosmetic texture/palette labels, declare singleton controls, or silently normalize invalid values. These obscure what generation actually does.

**Probe.** Final override stage: `PASS`, unknown keys rejected, no findings/warnings. Task tests explicitly check lower/upper boundaries and invalid calls.

## D7 — Declare fixed-transform rivals precisely

**Choice.** `SEMANTIC_RIVALS` and `LESSON_COMPETITORS` contain identity plus all seven non-identity D4 constants. `CANONICAL_SHORTCUTS` contains only `always_r1`.

**Rationale.** All canonical outputs happen to be clockwise rotations, but only that constant rule fits every canonical pair. Overdeclaring all rivals as canonical shortcuts was caught by a failing regression before the final version.

**Probe.** Exact canonical shortcut test and 100-per-band lesson census.

**Failure mode/limit.** Named rivals are finite. They cover the obvious canonical shortcut and wrong fixed transforms, not every possible program.

## D8 — Build a reusable independent ambiguity probe

**Choice.** Add `workspace/transform_ambiguity_probe.py` with JSON output, source hash, per-band counts, profiles, violations, and explicit limits.

**Rationale.** The shared baseline gates did not identify that 42.2% of labels were underdetermined by pixels. A task-local independent implementation avoids trusting the generator's own analyzer.

**Alternatives considered.** One-off notebook/snippet or only unit tests. A CLI artifact is replayable by future agents and produces compact review evidence.

**Probe.** The tool itself is imported and exercised by a task test; final 500-per-band run exits zero.

## D9 — Preserve failed/interrupted evidence

**Choice.** Retain the completed failing baseline, the initial interrupted run, and the stopped intermediate profile-coupled after run separately from the final green battery.

**Rationale.** An interrupted aggregate is not a pass, and the intermediate schedule had a real shortcut despite several green stages.

**Failure mode/limit.** Large redundant runtime copies are omitted from the return; decisive reports and reproducers are retained.
