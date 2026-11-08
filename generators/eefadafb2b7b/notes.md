# Working notes: eefadafb2b7b

## 2026-10-20 request-contract repair and parametric prototype

- Prior accepted return `review-821830bda6d02e60:v0001` was used only as a design lead; current measurements were rerun against the pinned packet source.
- Final generator SHA-256 is `68be4a4a51650f17e612f4edc8066b331717a659a8b0571ad6dbc687191da15a`; canonical `RULE_HASH` remains `1d44fc0f4360` and no Racket authority changed.
- A pre-generation request gate now rejects non-plain integer seeds/indices, negative indices, invalid difficulty scalars, coercible noninteger size overrides, invalid profile values, and unknown overrides.
- `counterexamples/request-contract-baseline.json` pins 224 lawful requests byte-for-byte (aggregate grid fingerprint `6c05b9cc04484978cea6323215375934130cca4ab406c3927ac745152a83a2f0`), so the contract repair does not change valid grids.
- Final source-bound checks: 12/12 after-battery stages green; 48/48 portable task tests pass; profile floor is 60/60 exact/envelope; override matrix is 4,680/4,680 accepted with zero findings.
- Production lessons use four ordered demonstrations plus one fixed query. A 300-lesson census found 0 production ambiguities, but unsupported leave-one-out rotations were ambiguous in 638/1,500 cases; do not claim arbitrary query rotation support.
- `workspace/parametric/` now contains a separate proposed `connectivity ∈ {8,4}` episode prototype. The default 8-connected Racket is exactly canonical; both complete settings execute in Racket and are distinguished by a demonstration. This is not a production axis or approval change.

## 2026-10-02 generator review

- Baseline ordinary dimensions had zero canonical-profile support and changed valid override ranges by difficulty.
- Degenerate texture values were mixed into the declared valid texture domain, and unknown overrides were silently accepted.
- The negative branch first sampled cyan and then deleted cells from accidental bridges, creating label-dependent cleanup artifacts.
- All eight canonical pairs are also fit by a 4-connected rule. They are also fit by a component-bounding-box shortcut. Both are now declared as `CANONICAL_SHORTCUTS` and receive constructive counterexamples.
- The selected bound Racket target was behaviorally equivalent but source-divergent. `racket_target.target_code` was synchronized exactly to the canonical selected `program_solution`; no rule semantics changed.
## Current reviewer considerations

Source SHA-256: `68be4a4a51650f17e612f4edc8066b331717a659a8b0571ad6dbc687191da15a`.

# Decisions: eefadafb2b7b — review-544a4199ee12ccaa

Final generator SHA-256: `68be4a4a51650f17e612f4edc8066b331717a659a8b0571ad6dbc687191da15a`.
Canonical rule hash: `1d44fc0f4360` (unchanged).
Prior lead consulted: accepted return `review-821830bda6d02e60:v0001`; all claims used here were remeasured against the packet’s pinned source.

## D9 / R1 — Validate the request before permissive generation helpers

**Choice.** Add `_validate_request` at the beginning of `generate`. Accept only plain Python integers for `seed`; nonnegative plain integers for `sample_index`; `None|easy|medium|hard` for difficulty; plain integers within the declared bounds for `grid_h` and `grid_w`; exact declared strings for `lesson_profile`; and no unknown overrides.

**Why.** The before battery had one blocking stage: defect lint reported 75 strict-scalar warnings. The permissive context layer accepted values such as `True`, floats, numeric strings, negative indices, and invalid difficulty scalars. That creates aliases in supposedly deterministic training data and makes axis contracts misleading.

**Alternatives rejected.** Coercing values explicitly would preserve the defect under a clearer name. Validating after `gen_ctx` would be too late because type identity and malformed values could already have been normalized. Editing the shared helper was outside this task-local patch.

**Probe and failure mode.** `tests/test_request_contract.py` rejects the malformed classes and is included in the 48-test portable task suite. Final defect lint reports zero findings. The validator intentionally does not change grid semantics or sampling for valid calls.

## D10 / R1 — Pin valid behavior before changing the contract

**Choice.** Record 224 valid requests spanning default calls and every dimension/profile override combination across difficulty bands in `counterexamples/request-contract-baseline.json`; require exact grid equality, per-grid SHA-256 equality, and aggregate fingerprint `6c05b9cc04484978cea6323215375934130cca4ab406c3927ac745152a83a2f0`.

**Why.** The repair should reject malformed API inputs without silently changing already approved examples. A distribution-level smoke test alone would not detect a deterministic output drift on a valid request.

**Alternatives rejected.** Pinning only a few hand-picked examples was cheaper but weak against branch-specific changes. Regenerating expected values after the repair would defeat the purpose of the regression test.

**Limit.** The 224 cases are broad but finite; they do not prove equivalence for every integer seed. The source change is nevertheless isolated to request validation, and the full after battery is source-bound to the final hash.

## D11 / P1 — Prototype connectivity as the single small rule parameter

**Choice.** Build a separate proposed episode-level parameter `connectivity ∈ {8,4}` under `workspace/parametric/`. The default 8-connected setting is byte-for-byte the canonical Racket program; the 4-connected setting changes only the cyan component operator. Choose the value once per episode, keep object roles/rings/output logic unchanged, and include a diagonal-bridge demonstration before any query that depends on the distinction.

**Why.** Connectivity is a nearby meaningful rule change already implicated by a canonical-fitting shortcut. It changes the executed reasoning step while preserving the family’s two red blocks, cyan components, and “one component touches both rings” relation.

**Alternatives rejected.** Output-color, grid-size, and profile parameters would be cosmetic or input-distribution knobs rather than rule changes. Resampling connectivity per pair would make the hidden episode rule incoherent. Adding it to production would violate the packet’s fixed canonical-rule boundary.

**Evidence.** `checks/parametric/eefadafb2b7b-connectivity-v1/report.json` records two complete episodes, both exact Racket programs, program hashes `18feebb9…` (8) and `322c5019…` (4), 8/8 canonical labels under the default, and a demonstration that distinguishes the rival in each episode. Public files omit parameters, programs, and query outputs.

**Status and limits.** **Prototype / proposed only.** It is not a production axis, approval refresh, canonical rule change, or training-admission claim. Evidence covers two settings and fixed four-input episodes, not undeclared rival families or all seeds.

## D12 / L1 — Preserve the ordered four-profile production curriculum; report rotations separately

**Choice.** Keep the existing four demonstrations in their cyclic profile order and the downstream fixed query policy. Do not redesign the generator merely to make every leave-one-out reassignment identifiable.

**Why.** The final source produced 300/300 valid fixed-query lessons (100 per band), 1,500 pairs, 1,408 unique inputs, zero production ambiguities, zero production hook warnings, and zero scoring/materialization errors. The task’s lesson contract deliberately requires all four decisive profiles in the demonstrations.

**Counterevidence retained.** A stricter required-rotation census found 638 ambiguous rotations out of 1,500 and 900 rotation hook warnings; it exits 1 and remains in `checks/lesson-census.json`. The same source-bound run with `--rotation-policy diagnostic` is retained as `checks/lesson-census-diagnostic.json`: production status is `no_ambiguity_found`, rotation status remains `ambiguous`, and exit is 0.

**Alternatives rejected.** Expanding every lesson enough that every pair can be held out would increase episode length and duplicate profiles for a downstream policy that does not rotate queries. Ignoring the rotation result would overstate robustness. The chosen policy reports the limitation rather than claiming arbitrary ordering support.

## D13 / R1 — Do not change Racket authority or valid-grid distribution

**Choice.** Leave the canonical Racket text, `RULE_HASH`, profile schedule, dimensions, and valid generated grids unchanged. The only canonical-path change is malformed request rejection.

**Why.** Rule smoke, authority sync, semantic gate, profile floor, override matrix, and the valid-call fingerprint all showed no semantic repair was needed. The assignment’s approved baseline already had a strong constructive curriculum.

**Self-review.** The new gate cannot create a label shortcut in valid grids because it runs before generation and emits no grid features. It can reject callers that previously relied on undocumented coercion; that is the intended contract correction.

## D14 / A1–A2 — Keep audit targets evidence-only

**Choice.** Reproduce and document the ignored-axis defect in `612b4efbecf0` and the portal-teaching defect in `4cea2727fcf9`, but make no source changes to either.

**Why.** The assignment explicitly separates adversarial audits from the selected repair. The reproducers and source hashes in `AUDIT.md` are sufficient for follow-up ownership without expanding the allowed patch scope.

## 2026-10-24 native connectivity promotion — review-faca37a9638144eb

- Promoted the retained `connectivity ∈ {8,4}` proposal to a native adapter. The default `8` program is byte-for-byte canonical; `4` changes only the cyan component constructor from `objects-8` to `objects`. The production generator remains unchanged at SHA-256 `68be4a4a51650f17e612f4edc8066b331717a659a8b0571ad6dbc687191da15a`.
- The native sampler now supports independent 2–6 demonstrations and 1–4 queries with matched inputs across settings, count-stable prefixes, four distinct queries, strict request typing, and a substantive 30×30 query containing 151 nonzero cells.
- Adversarial lesson review initially found that `smallest_component_8` fit the three visible demonstrations for the 4-connected setting and changed a query. The sampler now reserves an isolated cyan singleton in every scene. A second review found `bbox_bridge_4` still survived; every scene now also carries a moat-separated 4-connected outer frame whose bounding box spans both red rings. After these repairs, the first three demonstrations leave only the intended rule among the ten declared finite candidates for both settings.
- Reusable audit: `workspace/parametric/self_audit.py`. Current evidence covers 8 jobs, seeds 0/17, demo boundaries 2/6, all four queries, 128 protected-Racket labels, matched-input and prefix checks, and 16 one-query public projections.
- Native qualification is source-bound at `checks/eefadafb2b7b/qualification/qualification.json`: 2 settings × 2 seeds, 4 jobs, 32 protected-Racket labels, status `qualified`; training admission remains false.
- Required causal dependency: Step A partitions cyan cells under the episode-selected adjacency; Step B asks whether one derived component touches both red rings. In the retained 4-connected witness the two diagonal bridge cells are separate and the answer is `[[0]]`; replacing that intermediate with the 8-connected partition merges them and changes the protected-Racket answer to `[[8]]`. Evidence: `checks/eefadafb2b7b/causal/witness.json`.
- Status is reviewer-ready only. Exact-source owner acceptance and any downstream training decision remain pending; finite rivals and finite seeds do not prove universal identifiability.
