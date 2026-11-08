# Current design notes: `b88894a36787`

## Current native prototype — review-6f8d40b6d88b8c68

Production v3.1.0 and exact canonical SHA-256
`c26c5440739144d42a78c5bf4436b93299a3bea88ac220ea2f8388a006b034a5`
are unchanged. The native adapter reuses the inherited bottom/penultimate rules
and adds first-hit extension. A renders matched L-routes with leftmost-header
priority; B uses that immutable grid to stop unmatched columns before their
first obstacle, with bottom fallback. Two protected counterfactual cases show
that reading original edge dots instead changes the output.

Only the separate prototype admits 8–30 rectangular grids, 2–8 headers,
zero to two missing matches, crossing routes and up to two ignored edge dots.
At least one header matches. See the prototype README for exact count, type,
color and geometry limits. Requests use independent 3–6-demo/1–4-query prefixes;
ordinary qualification uses three demonstrations and four queries.

Self-review reversed the initial lesson geometry. Shared reflection did not
ensure opposite absolute canvas halves, and all shown collisions were shallow.
Protected Racket confirmed a right-half-stop shortcut at seed 0 and a
deep-stop shortcut at seeds 0, 17 and 19. D1 now has first/later crossings at
h-4/h-2; strict start intervals put D1/D2 hits on opposite canvas halves.
The three-demo count and all query inputs remain unchanged. Original evidence
and snapshots are retained under `checks/b88894a36787/`; a 56-execution replay
now refutes all four original finding rows by a repaired demonstration.

Final evidence: 82 focused tests, 82/82 finite rival comparisons demo-refuted,
30 maximum-count protected labels, six native-qualified jobs/78 evaluations,
two replayed causal cases, and 24 native public views with all three targeted
corruptions rejected. The maximum-seed 30×30 case spans all four boundaries
with 266–276 nonzero output cells across settings. These are finite checks.
The current manifest binds the adapter, resources, tests and scoped evidence.
No unresolved production hold appears in the current review index; inherited
resolved audit material is historical, not a newly cleared finding.

The legacy setting-named public writer is retired from current usage; its
files remain historical provenance. Native hash-named one-query files are the
model interface. The controller keeps the private bundle and future queries.
Next action: owner native qualification and fresh acceptance of these exact
integrated sources. Reviewer readiness grants no training admission.

## Inherited production history

## Intended rule

Row 0 contains one contiguous run of 2–4 distinct colors. For each header color:

- if one matching dot exists on the left or right edge, draw vertically from the header to that row, then horizontally to the edge;
- if no matching dot exists, extend that header column to the bottom row.

At most one header color may lack a dot. Generated paths are pairwise disjoint. The selected Racket program is the sole label authority; Python `_prediction` and rivals are diagnostics only.

## Current sampler (`VERSION = 3.1.0`)

Exact observable axes are `grid_h=11..15`, `grid_w=11..15`, and `n_markers=2..4`. Unknown keys, non-exact-integer controls, invalid difficulty, negative/non-integer `sample_index`, and non-exact-integer `seed` are rejected before generation.

The eight-slot schedule is:

1. left-interior missing, row-2 witness;
2. right-interior missing, row-2 witness;
3. left-interior missing, row-2 witness;
4. boundary missing, one-side routing;
5. left-interior missing, row-2 witness;
6. complete split sides with a legal shared row;
7. left-interior missing, row-2 witness;
8. complete one-side routing.

Slots 0/2/4/6 and slot 1 expose both horizontally reflected four-header interior omissions. Explicit `n_markers` overrides still take precedence; the production default uses four markers in the discriminator slots.

## Reversed decision

**Prior choice:** version `3.0.0` exposed only one interior missing position for four-header lessons. A geometry-based rival could guess the missing position from which side edges contained dots, fitting all canonical pairs and all sampled old generations.

**New choice:** retain the old right-interior case and add its lawful left-interior reflection in four schedule slots. Register the exact rival as `assumed_missing_position` in `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`, with witness `left_interior_missing_dot`.

**Reason/evidence:** the retained source-matched counterexample under `counterexamples/review-45ba7e74d228c452-v0001/` is accepted by the domain and protected Racket disagrees with the rival in 17 cells. Final fixed-seed and production lesson censuses refute the rival in every checked lesson/rotation.

A second repaired defect was permissive seed handling. The before defect lint accepted booleans, floats, and strings; version `3.1.0` requires `type(seed) is int`.

## Authority decision

No reference rule changed. `RULE_HASH` remains `94000a617419`; canonical selected program SHA-256 remains `c26c5440739144d42a78c5bf4436b93299a3bea88ac220ea2f8388a006b034a5`. The selected base rule text remains synchronized with canonical authority.

## Semantic support

Declared rivals are:

- `only_existing_pairs`: omits a header with no side dot;
- `all_columns_to_bottom`: ignores side dots and extends every header column;
- `assumed_missing_position`: guesses the unmatched header from edge geometry.

Final evidence on source `a1c23dd3749c259bca1a5439cc8be2e60d775b93fac15f6b01c0224aaf13feba`:

- strict battery: 12/12 green;
- portable task tests: 51/51 passed;
- semantic sample: 12 lessons / 48 rotations, no ambiguity;
- fixed seed 0 period census: 24 lessons / 96 rotations, no ambiguity;
- production census: 300 lessons / 1,200 rotations / 1,200 unique inputs, no ambiguity, warnings, or scoring errors.

## Parametric proposal

`workspace/parametric/missing_extension.py` proposes one episode-level setting:

- `bottom` (canonical/default): unmatched column reaches `h-1`;
- `penultimate`: unmatched column stops at `h-2`.

All other reasoning and object roles are unchanged. The setting is selected once per episode. Protected-Racket evidence under `checks/parametric/missing-extension-final/` shows exact canonical parity for `bottom` and that every demo/query distinguishes the two settings. This prototype is not wired into selected generation and has no approval status.

## Tests and reusable tools

- `tests/test_generator.py`: authority, canonical pairs, exact overrides, strict scalars, destructive validator mutations, distribution branches, noncrossing paths, rival contracts, retained counterexample, schedule rotations, and hash-seed determinism.
- `tests/test_parametric_missing_extension.py`: strict setting/seed contract, canonical program identity, episode consistency, Racket-separating lessons, and public/private separation.
- `workspace/reference_probe.py`: independent header parser and geometry diagnostics retained from the prior repair.
- `workspace/parametric/missing_extension.py`: runnable two-setting episode builder with protected-Racket evidence.

## Known limits and open findings

- Finite declared-rival checks do not prove unique induction against every possible hypothesis.
- The 300-lesson census samples production seeds; the period census exhausts starts/rotations only at seed 0.
- The selected sampler intentionally excludes path intersections, so first-match behavior at overlapping paths is not taught.
- The parametric proposal has only two settings and one retained episode per setting; it remains proposed, not selected or training-approved.
- Passing review checks does not change catalog approval or training admission.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-b13f407456697e19:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `f48c47e415fe1f50d73083b96f597645c3b50e646388c3b76bcca7c1dcb81057`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Resolve exact old-source missing-position finding on accepted a1c23dd3/version3.1.0. Reflected left-interior missing position now emitted in four of eight schedule slots; assumed_missing_position is registered/refuted with exact retained witness. Reported51 tests,24 fixed-seed period lessons/96 rotations and300 production lessons/1200 rotations address this witness. Canonical Racket unchanged;no owner rerun or universal guarantee.

### Assessment or prior finding

## b88894a36787

**A-b888 — Reproduced sampler-reflection shortcut caused by an unreachable missing-header position.**

Source binding: generator SHA-256 `f48c47e415fe1f50d73083b96f597645c3b50e646388c3b76bcca7c1dcb81057`; executed/catalog rule hash `94000a617419`; callable text SHA-256 `cfaccac5402b5f9ce3073b162300eb18f80b53b6f4ce5d4f1588fc33ca1f2bdf`.

For four header colors, schedule phase 0 always omits index `n // 2 = 2`; phase 2 omits only boundary index 0 or 3; phases 1 and 3 omit none. Interior missing index 1 therefore has zero sampler support even though the documented noncrossing domain is horizontally symmetric.

The reproducer generates `seed=0, sample_index=0, grid_h=11, grid_w=11, n_markers=4` and horizontally reflects every row. The reflected input has header colors `[5,4,6,7]`, side dots `(2,10,7)`, `(3,10,6)`, `(7,0,5)`, and missing header index 1. `self_check` returns `[]`. Public Racket execution extends color 4 to the bottom, while the shortcut `assumed_missing_position` guesses index 2 from the observed side geometry. The outputs differ in 17 cells.

The shortcut fits 4/4 canonical pairs and all 128 measured generated four-marker samples across four difficulties, four seeds, and eight sample indices when compared with the target's diagnostic mirror. The counterexample is lawful but sampler-unreachable. This is a distribution/teaching defect, not a label error.

Evidence:

- `checks/audit/b88894a36787/probe.py`
- `checks/audit/b88894a36787/prepared.json`
- `checks/audit/b88894a36787/base_input.json`
- `checks/audit/b88894a36787/input.json`
- `checks/audit/b88894a36787/racket.json`
- `checks/audit/b88894a36787/counterexample.json`

Suggested follow-up: sample both interior missing positions for four-header layouts, for example by reflecting lawful phase-0 layouts, declare the retained shortcut as a competitor, and rerun the complete schedule/query-rotation census. No patch was applied.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-b13f407456697e19-v0001/audit_assets.json), manifest SHA-256 `9c0d4e1419d82cc8440789313793d6000033c73b0abb014cd76cb86d5f81fb7e`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `a1c23dd3749c259bca1a5439cc8be2e60d775b93fac15f6b01c0224aaf13feba`.

# Decisions for `b88894a36787`

All final selected-generator measurements refer to assignment `review-1bf7bca8ee5c6089` and source SHA-256 `a1c23dd3749c259bca1a5439cc8be2e60d775b93fac15f6b01c0224aaf13feba`.

## D1 — Treat the prior shortcut audit as a lead, not as current measurement

**Prior choice/rationale:** version `3.0.0` used a four-slot schedule. Its rationale for choosing only one of the two reflected interior-missing cases was not recorded. Retained audit `review-45ba7e74d228c452:v0001` reported that a geometry-based rival fit all canonical and generated examples.

**New choice:** reproduce the rival exactly in task-local tests and make it a first-class executable contract.

**Alternatives:** trust the audit without reproduction; discard it and search only from scratch; or use it to choose a focused probe. I chose the last option. The retained counterexample was loaded from the task's own evidence, its source binding checked, and the behavior re-expressed in focused tests.

**Evidence:** `tests/test_generator.py::test_assumed_missing_position_is_declared_and_fits_all_canonical_pairs` and `::test_retained_reflection_is_a_lawful_counterexample_to_missing_position_shortcut`.

**Limit:** the prior receipt was generated against the baseline source, so final claims rely on current tests and current semantic censuses rather than historical acceptance.

## D2 — Repair the schedule by adding the horizontal reflection, not by randomizing

**Prior choice:** for a four-color header with one missing side dot, the sampler exposed the right-interior omission (index 2) but not the left-interior omission (index 1).

**New choice:** use an eight-slot deterministic period. Slots 0, 2, 4, and 6 force four headers and omit index 1; slot 1 retains index 2; the remaining slots preserve boundary-missing, split/shared-row, and complete one-side branches.

**Alternatives:** randomize the missing index; alternate only the two interior cases; or add a one-off adversarial fixture outside production. Random sampling can omit a discriminator in a lesson; a two-case schedule would narrow existing geometry coverage; a fixture alone would not repair exported lessons. The eight-slot schedule preserves existing branches while making the reflected witness unavoidable across the declared census.

**Evidence:** `checks/after-final/checks/b88894a36787_after_semantic_gate.schedule-census.json` covers 24 band/start lessons and 96 rotations; `checks/final-handoff-census.summary.json` covers 300 production lessons and 1,200 rotations.

**Limit:** fixed period coverage at seed 0 is not all-seed proof; the production census is finite.

## D3 — Reject non-exact-integer seeds before `GenCtx`

**Prior choice:** `seed` was passed directly to `gen_ctx`, which accepted booleans, floats, and numeric strings in the defect probe.

**New choice:** require `type(seed) is int`, mirroring the existing strict treatment of advertised integer axes. Keep `sample_index` a nonnegative exact integer.

**Alternatives:** coerce with `int(seed)` or rely on downstream validation. Coercion would collapse distinct invalid API inputs and hide caller mistakes; downstream acceptance is exactly the baseline defect.

**Evidence:** `checks/before/checks/b88894a36787_before_defect_lint.log` reports 15 accepted invalid seeds; the final defect-lint log reports `FLAGGED 0`; five parametrized scalar cases are covered by focused tests.

**Limit:** this repairs the public call contract only; it does not change deterministic keyed RNG behavior for valid integers.

## D4 — Declare the rival in all contracts with their distinct meanings

**Prior choice:** the shortcut was absent from the selected source's semantic declarations.

**New choice:** register `assumed_missing_position` in `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`, and map it from witness `left_interior_missing_dot` in `WITNESS_RIVALS`.

**Alternatives:** list it only as a generic lesson competitor or only as a canonical shortcut. It is both: it exactly fits all four unique canonical pairs and is a task-domain executable rival whose counterexample must be scheduled.

**Probe/failure:** the first after battery retained at `checks/after/` failed because `WITNESS_RIVALS` named the rival before `SEMANTIC_RIVALS` contained it. A new declaration-consistency regression failed first, then passed after the single metadata correction.

**Limit:** category membership verifies this one function, not all possible canonical-fitting heuristics.

## D5 — Preserve the canonical Racket authority

**Prior choice:** the selected canonical rule already correctly handles missing dots by extending the unmatched header column to the bottom.

**New choice:** make no Racket change. Repair only generation, validation, diagnostics, and tests.

**Alternatives:** change the authority to match the old sampler's narrower behavior or add special cases. Both would reverse the actual canonical rule to accommodate a curriculum defect.

**Evidence:** final authority sync and rule smoke are green; `RULE_HASH` remains `94000a617419`; canonical program SHA-256 remains `c26c5440739144d42a78c5bf4436b93299a3bea88ac220ea2f8388a006b034a5`.

**Limit:** the Python `_prediction` remains a diagnostic mirror, not a label authority.

## D6 — Use `missing_extension` as the bounded parametric proposal

**Purpose:** satisfy the original-family parametric priority with a nearby rule change that preserves object roles and reasoning structure.

**Choice:** vary only the terminal row of an unmatched header column: `bottom` (`h-1`, canonical) versus `penultimate` (`h-2`). Choose once per episode by SHA-256 and hold it fixed across demonstrations/query.

**Alternatives:** vary path direction, edge matching, color correspondence, or first-match priority. Those alter core relations or introduce multiple interacting parameters. Varying the unmatched terminal row is one bounded count/location parameter with an exact canonical default.

**Evidence:** `checks/parametric/missing-extension-final/evidence.json` is bound to final generator source. Both Racket programs label all pairs; every demonstration and query refutes the alternate setting; the `bottom` bytes equal canonical authority.

**Failure modes/limits:** only two settings and one episode per setting were retained; this does not establish learning quality across broad seeds. The variant is proposed only and is not wired into production generation.

## D7 — Keep peer audits findings-only

The two assigned audit targets were not edited. For `4f640d81f260`, a compact current-source probe and strict semantic audit reproduce invalid shortcut declarations, and portable test preflight reproduces legacy-path failures. For `27c1546d634f`, a 600-sample probe independently reproduces two curriculum shortcuts and ignored controls, while protected Racket supplies the irregular one-hole counterexample. These are intake findings, not approvals or repairs.
