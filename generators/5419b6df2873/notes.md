# Current notes: 5419b6df2873

## Current native parametric return — contact-color row relay

The production generator and selected canonical Racket authority remain unchanged
(generator SHA-256 `c4e535bb132fe37ce44dd9777375c16f698f06229635cbcb0678b1e6985e52a6`;
canonical parametric source SHA-256
`58ef77026707a2132e026402bfbc93d882a8618da7d7b749c954a7fbfc44448a`).
The task-local native family now has two episode-fixed settings:

- `columns_only`: the exact canonical fresh-canvas column expansion.
- `contact_color_rows`: first expand the top-row markers into columns; then use
  the unique lower color-9 probe newly touching an expanded column to derive a
  marker color, and fill remote payload rows carrying that color.

This alternative has a non-collapsing input-dependent dependency. Step A creates
the column field; the intermediate is the contacted marker color plus its remote
payload rows; Step B consumes that result to choose which rows to fill. Before
Step A every color-9 probe has zero horizontal neighbors, so the row action cannot
be selected from the original grid. The retained protected-Racket wrong-order
witness chooses color 4 only after expansion and changes the final output when A
is skipped/reordered.

A 64-seed authoring audit covered both settings, demonstration counts 2, 3, and
6, all four queries, 14 finite rivals, both probe sides, selected colors 2–7, and
sizes through a substantive 30×30 boundary case: 384 episodes, 2,944 labeled
pairs, 640 distinct inputs, and zero failures. During that sweep, seed 19 exposed
a sampler bug where two decoy probes could be horizontally adjacent, allowing the
wrong-order ablation to observe color 9 before Step A. The sampler now places all
color-9 probes nonadjacently, with a regression asserting pre-Step-A inertness.

Native qualification retained four jobs (settings × seeds 0 and 17), 40
protected-Racket label executions, exact source binding, and only the intended
setting surviving each lesson. The task suite passes 47 tests. Public evidence
contains eight hash-named one-query challenges, positive privacy/schema checks,
and a deliberately leaked-answer file rejected by the checker. Evidence: 
`workspace/parametric/evidence/manifest.json`,
`workspace/parametric/evidence/current/self-audit.json`,
`checks/5419b6df2873/qualification/qualification.json`, and
`checks/5419b6df2873/causal/witness.json`.

Disposition: reviewer-reported native-ready, owner acceptance pending. This is
not training admission, measured training benefit, or a proof of universal
identifiability; the learnability claim is limited to the retained finite rivals.

## Intended rule

Each nonzero first-row cell marks a column. Start from a fresh all-zero grid of the same shape and fill every marked column with its marker color. Unrelated lower-row input cells are erased, not copied. The selected canonical Racket authority is unchanged and pinned by `RULE_HASH="72e1b062f409"`.

## Reversed prior choices

- **Prior:** lower-row noise was probabilistic, so an ordinary three-demo lesson could leave the canonical-fitting `preserve_lower_cells` rival alive. Lead: source-matched retained audit `review-997293e370055e7c:v0001` (ZIP SHA-256 `970ce72e515d4ff74742def3714d72e033d92f8e2ad565b5167c2f0d8baea2ad`). **Now:** every production sample has one colored lower-row cell in an unmarked column, reusing a marker color; the selected rule erases it and the rival preserves it.
- **Prior:** the public axis surface contained controls that were ignored, weakly validated, or not directly observable. **Now:** only exact `grid_h`, `grid_w`, and `n_markers` remain; all round-trip through `observe_overrides` in every band.
- **Prior:** scalar calls and grid validation were permissive. **Now:** seed/index/difficulty/override names and types are strict, and `self_check` validates the complete declared teaching grammar.
- **Prior:** difficulty could be observationally dead. **Now:** all bands retain the same five exact canonical profiles but salt layout/color/witness random streams by normalized band.
- **Prior:** no executable semantic contract named the strongest shortcut. **Now:** one shared rival callable appears in `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS`, with witness `erased_unmarked_cell` and a label-checking `lesson_identifiable` hook.

## Current distribution and lesson policy

Version `3.0.0` cycles five exact canonical `(height,width,marker-count)` profiles:

`(6,8,3), (7,9,2), (5,10,3), (8,8,2), (7,11,3)`.

A lesson uses three consecutive demonstrations plus one query. Arbitrary held-out query rotations are supported against the declared rival. Every generated input has 2..5 distinct first-row marker colors, at least one unmarked column, and one lower-row erasure witness in an unmarked column.

## Evidence

Final generator SHA-256: `c4e535bb132fe37ce44dd9777375c16f698f06229635cbcb0678b1e6985e52a6`.

- Final battery: 12/12 green with required rotations and all five fixed-seed schedule starts enumerated (`checks/after-final/result.json`).
- Portable focused tests: 30/30 (`checks/task-tests-final-v2/result.json`).
- Large census: 300 lessons, 1,200 pairs, 1,200 rotations, 0 production/rotation ambiguity or error (`checks/lesson-census-final.json`).
- Exact Racket-checked counterexample and finite 300-input emission probe: `checks/shortcut-probe.json` and `counterexamples/review-f052cb7cb3f5a69a/preserve-lower-cells.json`.
- Proposed, non-production `lower_cells={erase,preserve}` prototype: `workspace/parametric/`; 8/8 protected-Racket pair checks and all six train pairs distinguish the chosen episode setting (`checks/parametric/report.json`).

## Known limits and open findings

The evidence is finite and targets the declared strongest canonical-fitting rival; it is not a proof of unique induction against every program. Difficulty changes randomized surface content rather than proven reasoning depth. The parametric alternative remains a research prototype and is not selected authority or training approval.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-997293e370055e7c:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `99e9e32df4720637ec43e8b31c6d8d5fb0d9dd9f1804f3621c99bf9079851e61`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted source SHA c4e535bb132fe37ce44dd9777375c16f698f06229635cbcb0678b1e6985e52a6 constructs an unmarked-column lower-cell erasure witness in every ordinary sample and declares preserve_lower_cells as an executable rival. tests/test_generator.py, tests/test_shortcut_probe.py, workspace/probe_shortcut.py and counterexamples/review-f052cb7cb3f5a69a/preserve-lower-cells.json retain regressions. Reviewer reports 300 production lessons and 1200 rotations with zero ambiguities plus all five fixed-seed starts. Explicitly resolve the original probabilistic-witness finding on reviewer-reported evidence; no maintainer rerun.

### Assessment or prior finding

## 5419b6df2873

**Reproduced defect — an ordinary three-demo lesson can leave “preserve lower-row noise” indistinguishable from the intended fresh-output rule.** Source SHA-256: `99e9e32df4720637ec43e8b31c6d8d5fb0d9dd9f1804f3621c99bf9079851e61`.

The intended rule builds a fresh zero grid and fills every column whose top cell is a marker. A plausible rival instead copies the input, fills those marker columns, and preserves lower-row cells in unmarked columns. For difficulty `easy`, seed `1`, and sequential sample indexes `9,10,11,12`, that rival fits all first three labeled pairs but changes the fourth. The first three inputs contain no lower-row nonzero cell in an unmarked column; the query contains colors `2` and `4` at zero-based `(3,4)` and `(4,4)`. The canonical rule erases both, while the rival preserves them.

This is not only a Python-mirror suspicion. `checks/audits/5419b6df2873/racket-output.json` applies the canonical Racket authority to all four exact inputs and matches the independently reconstructed intended outputs. `checks/audits/5419b6df2873/reproduction.json` records the source hash, generation arguments, all inputs/outputs, rival outputs, and fit vector `[true,true,true,false]`; `checks/audits/5419b6df2873/reproduce_preserve_noise_shortcut.py` regenerates and asserts the witness. A repair should schedule at least one unmarked-column noise witness into every declared lesson and declare this rival in the lesson contract, rather than relying on the current probabilistic noise branch.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-997293e370055e7c-v0001/audit_assets.json), manifest SHA-256 `4ecb401b28665b03149275295a266115e4817f28608d7f0cff56113a9263d0d0`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `c4e535bb132fe37ce44dd9777375c16f698f06229635cbcb0678b1e6985e52a6`.

# Decisions — 5419b6df2873

## D1 — Preserve the selected authority

**Prior choice:** the canonical Racket program creates a fresh zero grid and fills columns whose first-row cells are nonzero. The rationale for that original rule is not documented in this packet.

**Decision:** keep the canonical row and Racket authority unchanged and pin its normalized hash as `RULE_HASH="72e1b062f409"` in the generator. The defect was in generated teaching support and public contracts, not labels.

**Alternative rejected:** changing the rule to preserve lower-row content would make the old copy-then-fill shortcut authoritative, but would reverse the selected task rather than repair its curriculum.

**Probe/evidence:** final `rule_smoke`, `racket_lint`, and `authority_sync` stages are green in `checks/after-final/result.json`; the executable shortcut probe independently matched `authoritative_output` to protected Racket on the exact retained counterexample.

**Limit:** hash pinning and finite execution checks detect drift but are not a formal proof of semantic equivalence for all grids.

## D2 — Make erasure evidence constructive, not probabilistic

**Prior choice:** lower-row noise appeared only probabilistically. Prior audit `review-997293e370055e7c:v0001` showed a normal three-demonstration window with no erasure witness, leaving `preserve_lower_cells` alive. The original probability/rationale is unknown.

**Decision:** every generated input contains exactly one nonzero lower-row cell in an unmarked top-row column. The witness color is selected from the marker palette. Therefore the selected fresh-grid rule erases it and the copy-input rival preserves it.

**Alternatives rejected:** increasing the old noise probability, lesson-level rejection sampling, or placing a novel-color distractor. Probabilistic approaches still allow unlucky witness-free windows; a novel color could teach an unintended color-exclusion heuristic.

**Probe/evidence:** `checks/shortcut-probe.json` found 300/300 witness hits and rival disagreements across the three bands; `checks/lesson-census-final.json` found 0 ambiguities in 300 production lessons and 1,200 rotations. The exact example is retained under `counterexamples/review-f052cb7cb3f5a69a/` and covered by a portable regression.

**Failure modes/limit:** only the declared preserve-input rival is exhaustively targeted. Other undeclared programs could still fit finite demonstrations.

## D3 — Narrow public axes to exact observable controls

**Prior choice:** the pinned baseline advertised many controls that were ignored, weakly validated, or not recoverable. Original rationales are unknown.

**Decision:** expose only `grid_h=5..9`, `grid_w=6..11`, and `n_markers=2..5`. `observe_overrides` recovers all three directly from pixels; every endpoint is exact in every difficulty band.

**Alternatives rejected:** retaining decorative/ignored controls for apparent variety, or declaring difficulty-conditional override domains. Both would make the public API misleading.

**Probe/evidence:** focused override regressions cover low/high/interior tuples in default/easy/medium/hard. Final `override`, `defect_lint`, and portable task tests are green.

**Failure modes/limit:** the grammar permits up to three lawful lower-row witness cells for compatibility, while the production sampler emits exactly one. The observer intentionally reports public axes, not hidden random choices.

## D4 — Use the five exact canonical profiles as the schedule

**Prior choice:** the old support did not guarantee exact canonical profile coverage in every band.

**Decision:** cycle through `(6,8,3)`, `(7,9,2)`, `(5,10,3)`, `(8,8,2)`, and `(7,11,3)`, where the third value is marker count and zero is excluded. Set `LESSON_SCHEDULE_PERIOD=5` and name every slot.

**Alternatives rejected:** broad unconstrained shape sampling or one fixed canonical profile. The former weakens measured support; the latter removes useful shape variation.

**Probe/evidence:** final profile floor reports exact-profile `60/60` and envelope `60/60`. Fixed-seed schedule enumeration covered all five start residues in each band.

**Failure modes/limit:** the schedule is intentionally synthetic coverage, not an estimate of a natural data distribution.

## D5 — Let difficulty alter content without altering semantic coverage

**Prior choice:** difficulty labels were effectively dead in the first repaired draft because the same seed labels yielded byte-identical easy/medium/hard grids.

**Decision:** keep the same canonical profile schedule in every band, but include the normalized band in marker-layout, marker-color, and witness RNG labels. `None`, `default`, and `medium` normalize to `medium`.

**Alternatives rejected:** band-specific dimensions/marker counts, which would confound difficulty with canonical support; or retaining dead difficulty labels.

**Probe/evidence:** `checks/tdd-dead-bands-red.log` captured the failure; the final regression verifies distinct band emissions and identical profile observations.

**Failure modes/limit:** difficulty changes surface randomness, not intrinsic reasoning depth. This is explicit rather than claiming unsupported difficulty semantics.

## D6 — Declare the strongest canonical-fitting rival once

**Prior choice:** no executable semantic contract named the preserve-input shortcut.

**Decision:** one callable, `_preserve_lower_cells`, is shared by `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS`; witness `erased_unmarked_cell` maps to it. `lesson_identifiable` verifies labels and rejects lessons whose demonstrations leave a query-relevant rival alive.

**Alternatives rejected:** prose-only documentation or three independent rival implementations. Prose cannot be source-bound by the census; duplicate implementations can silently drift.

**Probe/evidence:** all 5 labeled canonical pairs fit the rival, while the retained exact generated input disagrees. The 300-lesson census and five-start fixed-seed census both report no production or rotation ambiguity.

**Failure modes/limit:** the finite registry is not a universal program search.

## D7 — Validate calls and grids strictly

**Prior choice:** booleans, negative indexes, unknown difficulties, misspelled axes, and invalid scalars could be accepted or coerced; `self_check` admitted non-task grids.

**Decision:** validate `seed`, nonnegative `sample_index`, normalized difficulty, override names/types/ranges, rectangular shape, ARC colors, top-row marker count/distinctness, unmarked-column availability, and lawful lower-row witness colors/locations.

**Alternatives rejected:** relying on `gen_ctx` coercion or allowing a permissive hidden validator. Explicit task-local errors are easier to test and audit.

**Probe/evidence:** focused TDD began with 21 expected failures (`checks/tdd-red.log`) and ended with 30 passing tests; final `lint`, `defect_lint`, `selfcheck`, `grammar`, and `override` are green.

**Failure modes/limit:** validation describes the declared teaching grammar, not every grid on which the mathematical rule could be executed.

## D8 — Keep the parametric rule separate from production

**Assessment:** `lower_cells ∈ {erase,preserve}` is a meaningful one-bit rule parameter because both settings fit the canonical all-zero-lower-row examples, and an unmarked-column lower cell distinguishes them.

**Decision:** build a runnable proposed prototype under `workspace/parametric/`, choose the setting once per episode, and materialize matching public/private episodes and Racket programs. Do not wire it into the selected generator.

**Alternatives rejected:** making the parameter vary per pair, which would destroy episode consistency, or silently replacing the selected authority.

**Probe/evidence:** `checks/parametric/report.json` checked 2 settings, 3 train + 1 test pair per setting, 8/8 protected-Racket labels, and 6/6 distinguishing train pairs. Program SHA-256 values are recorded in `REVIEW.md`.

**Failure modes/limit:** one seed and two settings were tested; the prototype is not training-approved.

## D9 — Lesson ordering and query policy

**Decision:** production uses three demonstrations in consecutive sampler order and the fourth pair as query. The repair additionally supports any held-out position: all four rotations must be identifiable against the declared rival.

**Probe/evidence:** the large census materialized 300 lessons and all 1,200 rotations with zero ambiguity/error. The five-start fixed-seed census exhausts declared schedule residues at seed 0.

**Limit:** fixed-seed residue enumeration does not certify every seed, and rotated evaluation does not prove uniqueness against undeclared hypotheses.
