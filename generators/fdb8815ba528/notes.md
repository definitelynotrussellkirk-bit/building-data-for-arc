# Working notes: fdb8815ba528

## 2026-10-08 — review-92897c2866644260, version 4.0.0

Selected baseline 3.0.0 SHA-256: `01d8c70469ed5c8b0244487321874e768d3ffcb0a9f7afb9cd26ad205f87bd66`.
Final generator SHA-256: `5ae411026b9bf754b508d0dcbf4cd533cb465f38e290de67ea4e29c18a984b73`.
Canonical rule hash remains `001f318153f4`; no Racket authority changed.

### Intended rule

On a fresh zero grid, replace each nonzero same-colour 4-connected component by the same-colour hollow perimeter of its tight axis-aligned bounding box. Components are processed independently. Source pixels strictly inside a bbox disappear; absent border pixels are added.

### Baseline findings

The selected source failed lint, self-check, defect lint, profile floor, and override stages. Its validator rejected a canonical input, most advertised controls were dead or overlapping, unknown overrides were silently accepted, and no executable semantic contract existed. Distinct-colour separated canonical examples left three component-partition shortcuts unresolved: one bbox per colour, same-colour 8-connectivity, and colour-blind 4-connectivity.

### Current design

Five exact axes are returned-grid-observable: `scene_profile`, `n_blobs`, `color_relation`, `edge_mode`, and `palette_kind`. All legal joint combinations are supported; invalid values and unknown keys fail loudly. The four-slot production schedule links real canonical dimensions/morphologies to generalized repeated-colour/contact scenes.

Three/four-component contact scenes include a diagonal-only same-colour pair and orthogonally touching different colours. Primary shapes guarantee a missing bbox-border cell and, in generalized scenes, an interior source cell. Eight witnesses and eleven rivals make the lesson contract executable. Four demonstrations are required.

The current same-rule task `cc8c719680e6` was consulted as an implementation-pattern lead for strict canonical profiles and connectivity counterexamples. No prior return for this selected baseline was used as measurement evidence.

### Verification

- Final battery: 12/12 green (`checks/after/`).
- Focused source-bound tests: 58/58.
- Exact-axis matrix: 3,456/3,456 (`checks/exhaustive-contract.json`).
- Lesson census: 300/300 materialized; 0 production ambiguities and 0/1,500 rotated-query ambiguities against declared rivals (`checks/lesson-census.json`).
- Retained authority-bound shortcut witness: `counterexamples/current-shortcut/question_training_shortcut.json`.

### Known limits

The component-shape bank is finite and generalized contacts occupy a bounded 5×5 core. Bbox footprints are deliberately nonoverlapping. Finite declared-rival checks do not prove universal identifiability or model performance; a larger morphology lookup remains possible in principle. Approval and training safety remain maintainer decisions.
## Current reviewer considerations

Source SHA-256: `5ae411026b9bf754b508d0dcbf4cd533cb465f38e290de67ea4e29c18a984b73`.

# Decisions for `fdb8815ba528`

## D1 — Repair the data distribution and contract, not the Racket rule

**Observed baseline.** Rule smoke and authority sync were already green, and an independent oracle matched all canonical outputs. Failures were in generation, validation, exact controls, profile support, and lesson semantics.

**Decision.** Keep canonical rule hash `001f318153f4` unchanged. Replace the selected generator implementation and bump `VERSION` from 3.0.0 to 4.0.0 because keyed generation output changes substantially.

**Rejected alternative.** Rewriting the Racket rule would add authority churn without fixing dead controls or ambiguous lessons.

## D2 — Replace broad/dead controls with five exact observable axes

**Prior choice.** The baseline advertised dimensions, object count/size, palette aliases, and several derived quantities. Many were ignored, overlapped, or not independently observable; the override battery produced over 9,500 findings and accepted an unknown key.

**Decision.** Expose only `scene_profile`, `n_blobs`, `color_relation`, `edge_mode`, and `palette_kind`. Every value is recoverable from the returned grid, all legal joint combinations are supported, and invalid/unknown values raise immediately. `observe_overrides` and the independent `workspace/reference_probe.py` observer provide two implementations.

**Probe.** `workspace/exhaustive_contract_probe.py` ran 3,456 legal combinations with zero failures (`checks/exhaustive-contract.json`).

**Rejected alternative.** Keeping legacy aliases for compatibility would preserve ambiguous semantics and make typo acceptance look like success.

## D3 — Link default schedule slots to real canonical profiles

**Decision.** The four default positions use the four canonical dimensions/morphology signatures: 8×9, 7×8, 9×9, and 8×10. Canonical-like slots preserve the linked component count, edge-contact property, and morphology multiset rather than independently shuffling those facts.

**Why.** Canonical acceptance is not production support. The baseline validator rejected a canonical example and the profile floor found no medium/hard support. Linked profiles make the supported branches explicit and measurable.

**Failure caught during TDD.** An initial 8×9 anchor sometimes placed the second object on the right edge while declaring `edge_mode="interior"`. The observer test failed; the placement was corrected rather than weakening observability.

## D4 — Teach component identity, not merely box drawing

**Decision.** Three/four-component scenes include (a) two disconnected components with the same colour that touch only diagonally and (b) a different-colour component touching one of them orthogonally. These cases distinguish per-component same-colour 4-connectivity from per-colour aggregation, same-colour 8-connectivity, and colour-blind foreground connectivity.

**Evidence.** All three wrong rules fit every canonical pair. The retained production-shaped counterexample differs from the authority output at 7, 7, and 15 cells respectively and is checked in the focused suite.

**Rejected alternative.** Merely adding more colours, positions, or random polyominoes would increase pixel diversity without creating evidence about the partition rule.

## D5 — Force both fresh-canvas additions and deletions

**Decision.** Primary shapes omit at least one bbox-border cell and include a source cell strictly inside the bbox. Correct outputs must therefore add border pixels and erase interior source pixels.

**Why.** This jointly refutes identity, “keep only existing border pixels,” “preserve the source then add a frame,” and solid-box filling. The shared semantic scan measured additions on 600/600 draws and true deletions on 288/600, in every difficulty band.

**Rejected alternative.** Shapes that only gain pixels leave overlay-on-source shortcuts alive; shapes that are already outlines make the transformation an identity.

## D6 — Use constructive, fail-loud validation

**Decision.** `self_check` validates rectangular ARC grids, 2–4 lawful components, nondegenerate 2D boxes, non-solid/non-already-framed shapes, nonoverlapping bbox footprints, and the exact allowed colour relation. It also compares requested overrides against observed values when metadata is supplied. Generation checks its own output and refuses internal mismatches.

**Rejected alternative.** Silent rejection sampling would hide unsupported control combinations and can bias or stall generation.

## D7 — Require four demonstrations and executable rivals

**Decision.** `EXAMPLES_NEEDED = 4`; a lesson must have correct labels and every declared competitor must be falsified by at least one demonstration. Four corresponds to the production schedule period and guarantees canonical-profile, repeated-colour, border/interior, and connectivity evidence in ordered lessons.

**Measured policy.** The large census uses four demonstrations plus one query. Production order and a required one-pair-held-out rotation of every labelled pair both show zero ambiguity against the declared rival set across 300 lessons / 1,500 rotations.

**Limit.** This is finite evidence against named rivals, not proof against every program. Removing demonstrations or inventing an undeclared curriculum assembly requires a new check.

## D8 — Retain independent reviewer tooling

`workspace/reference_probe.py` independently loads canonical pairs, extracts components, computes the oracle, observes axes, and implements the strongest rivals. `workspace/exhaustive_contract_probe.py` turns the whole legal joint axis space into replayable JSON evidence. These tools avoid circular tests that merely call production helpers.

## D9 — Keep conservative spatial limits explicit

The 5×5 contact core and finite connected-shape bank are deliberate constraints, not claims about the full ARC domain. Bbox footprints remain disjoint so independently drawn output boxes cannot overwrite each other. Global collision-free placement and a broader morphology bank are possible follow-ups only after a measured shortcut justifies the extra complexity.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-ef60e89ef8fcf034:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `5ae411026b9bf754b508d0dcbf4cd533cb465f38e290de67ea4e29c18a984b73`. At disposition, audited bytes match the current source.

### Current decision

Audited source is repo/generators/fdb8815ba528/generator.py, unchanged SHA256 5ae411026b9bf754b508d0dcbf4cd533cb465f38e290de67ea4e29c18a984b73. Explicit no_issue within documented restricted domain. Declared nonoverlap bbox grammar:58 portable tests pass, named rivals covered. Disjoint L components with overlapping bbox footprints expose row-major vsreverse paint precedence at2 cells under actualRacket, but self_check rejects overlap. No advertised-domain failure found; controlled overlap curriculum is a possible future extension, not an implemented repair. These are rejected-domain canonical-semantics diagnostics, not accepted-input/production defects. Do not infer universal coverage or approval from this disposition. Source-bound question retained in generators/fdb8815ba528/evidence/bounded-domain-ef60e89ef8fcf034/manifest.json. Quoted basenames mean these exact target-local paths: `checks/audit/fdb8815ba528-task-tests/RUNTIME_MANIFEST.json` `checks/audit/fdb8815ba528-task-tests/checks/task_tests.xml` `checks/audit/fdb8815ba528-task-tests/progress.log` `checks/audit/fdb8815ba528-task-tests/result.json` `checks/audit/fdb8815ba528/overlapping-bbox-witness.json` `checks/audit/fdb8815ba528/overlapping_bbox_probe.py`

### Assessment or prior finding

## fdb8815ba528

**Domain question / coverage restriction — overlapping bounding-box precedence
is not taught.** The 58 portable task tests pass, and the advertised grammar and
named rivals are well covered. The canonical Racket program nevertheless paints
component boxes sequentially, so different-color box borders that overlap have
an order-dependent output. Production rejects all overlapping bbox footprints,
therefore this composition behavior is absent from its lessons.

`checks/audit/fdb8815ba528/overlapping-bbox-witness.json` contains an exact 7×7
input with two disjoint L-shaped components whose tight bounding boxes overlap.
The selected Racket authority matches row-major component processing and differs
from a reverse-order rival at `(2,4)` and `(4,2)` (authority color 3 versus rival
color 2). The generator's `self_check` rejects the input solely because the bbox
footprints overlap.

This is not a failure inside the declared nonoverlap grammar. It is a concrete
unrepresented part of the canonical rule's composition semantics. A future
repair can either retain and explicitly document the restricted domain or add a
nonambiguous overlap curriculum with an executable reverse-order rival. No
audited source was edited.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
