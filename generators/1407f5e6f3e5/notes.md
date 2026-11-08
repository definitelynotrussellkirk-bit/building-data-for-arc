# Working notes: 1407f5e6f3e5

## 2026-10-07 review-db2283e10f17bf0f

The pinned v2.1.1 baseline had a correct Racket transformation but an invalid generator contract: no `RULE_HASH`, dead and impossible controls, retry placement that could return fewer components than requested, an acceptance-only `self_check`, weak canonical-profile support, and no semantic lesson contract. No prior task-local return was used as a repair lead; `evidence/associated_notes.jsonl` was empty.

Version 3.0.0 keeps the Racket authority unchanged and pins rule hash `c86a6d30fc9f`. It generates exactly 2–4 same-color 4-connected sparse objects by finite backtracking. Each object has 3–7 cells, a holed 2×2–3×3 box, and a box disjoint from every other box. Public controls are only `grid_h`, `grid_w`, `components`, and `repeat_color`; all are exact in every band and observable from pixels.

The strongest canonical-fitting shortcut is `global_color_bbox`: merge disconnected same-color cells before filling one box. The retained `counterexamples/global_color_bbox.json` disproves it. Default even indices emit repeated-color witnesses; odd indices alternate a canonical-profile anchor and broad sampling. With three demonstrations, every single-pair query rotation of a four-pair window retains at least one witness.

Final evidence for generator SHA-256 `1ab47ad075f4491c938a9d737440ea91ebec1e2eabd16c4095c45c6ef1e2357b`: 12/12 battery stages green; 10,980/10,980 override draws accepted with zero findings; 20/60 exact canonical-profile hits across all bands; 0/300 ambiguous production lessons and 0/1,200 ambiguous rotations; all 2 declared schedule residues × 3 bands also clean at the fixed census seed.

Known limits: the generated grammar is narrower than the full mathematical rule domain, and finite declared-rival checks do not prove unique induction against every program. The Python prediction helper is supplementary; selected Racket remains authority.
## Current reviewer considerations

Source SHA-256: `1ab47ad075f4491c938a9d737440ea91ebec1e2eabd16c4095c45c6ef1e2357b`.

# Design decisions for `1407f5e6f3e5`

Final generator SHA-256: `1ab47ad075f4491c938a9d737440ea91ebec1e2eabd16c4095c45c6ef1e2357b`.
No prior return was used as authority or copied as a repair lead; the task-local associated-notes file was empty. Decisions below were made from the pinned baseline, canonical pairs, current check tooling, and newly retained probes.

## D1 — Replace pseudo-axes with four observable controls

**Prior choice.** The baseline declared nine axes, including palette aliases, singleton enums, and broad numeric ranges. The original rationale is not documented; the comments suggest generic generator-template coverage rather than task-specific control semantics.

**New choice.** Expose only `grid_h`, `grid_w`, `components`, and `repeat_color`. Give every declared value exact support in every band, reject unknown/invalid values, and provide `observe_overrides()`.

**Alternatives considered.** I rejected retaining palette/texture aliases because color roles are irrelevant to this rule and the old values were byte-identical. I rejected band-specific incompatibility tables because the small constructive domain supports all joint combinations directly.

**Evidence.** Baseline override evidence contains 6,779+ representative findings plus 69,360 undeclared multi-axis rejections and an accepted unknown key. Final evidence has 10,980/10,980 accepted draws, 0 findings, and unknown-key rejection.

**Failure mode / limit.** The control surface is deliberately smaller. It does not promise independent controls for shape family, exact colors, or layout topology.

## D2 — Use finite constructive placement instead of bounded retries

**Prior choice.** The baseline tried up to 500 random placements and returned whatever count had been reached. This could silently violate the requested component count.

**New choice.** Draw all shapes first, enumerate legal placements, and solve the disjoint-one-cell-moat layout with finite backtracking. Verify the exact component count and repeated-color state from the returned pixels.

**Alternatives considered.** Increasing the retry count would reduce but not remove short draws. Rejection sampling the entire grid would obscure failure causes and make exact override support difficult to prove.

**Evidence.** Focused tests cover both axis boundaries in all four bands. The independent 1,200-draw probe found zero invalid scenes, and the override matrix found no short or mismatched materializations.

**Failure mode / limit.** Backtracking cost grows combinatorially outside the small declared domain. The generator therefore caps the canvas and component count instead of pretending to support arbitrary larger scenes.

## D3 — Define a compact structural grammar

**Prior choice.** Comments said “isolated components with bounding-box holes,” but `self_check` only checked nonempty rectangularity and otherwise accepted everything, including blank and solid impostors.

**New choice.** Require 2–4 same-color 4-connected components, 3–7 cells each, 2×2–3×3 holed bounding boxes, disjoint boxes, ARC colors, and at most one repeated color pair.

**Alternatives considered.** I rejected validating only generated shape-library membership because the canonical examples need not share exact library provenance. I also rejected allowing solid rectangles and empty grids in ordinary support because they make the transformation invisible.

**Evidence.** All 5 canonical inputs pass. The self-check gate keeps 60/60 defaults and rejects 40/60 destructive mutations. Defect lint reports zero findings.

**Failure mode / limit.** The selected grammar is a reviewed neighborhood of the canonical rule, not the full mathematical domain of every possible component-bounding-box puzzle.

## D4 — Add repeated-color scenes as the semantic axis

**Prior choice.** The baseline mostly used arbitrary component colors and had no explicit semantic rival, witness, or lesson hook. Canonical examples allow a solver to merge all cells of a color before taking a box.

**New choice.** Add `repeat_color`; teaching scenes contain two disconnected components with the same color and disjoint local boxes. Retain `global_color_bbox` as the canonical shortcut/rival and `repeated_color_components` as its witness.

**Alternatives considered.** More shape diversity alone does not separate per-component from per-color grouping. Overlapping boxes were rejected because paint order would introduce an unrelated conflict. Reusing more than one color pair was unnecessary for the target distinction.

**Evidence.** The retained counterexample is accepted by `self_check`, its expected output is reproduced by real Racket, and the rival differs. The public semantic gate and two larger censuses found no ambiguity against the declared rival.

**Failure mode / limit.** Only one named rival is encoded. Other program-synthesis shortcuts remain possible and must be added when identified.

## D5 — Period-2 curriculum with canonical anchors

**Prior choice.** There was no task-level schedule or guarantee that a lesson would include a semantic witness.

**New choice.** Even indices are repeated-color teaching scenes. Odd indices are ordinary; indices congruent to 1 modulo 4 are canonical-profile anchors. `EXAMPLES_NEEDED = 3`, and lessons are assembled from four consecutive labelled pairs (three demos plus one held-out pair).

**Alternatives considered.** A random witness probability was rejected because it permits ambiguous lessons. A four-profile schedule was unnecessary: alternating witnesses already guarantees that any single query rotation leaves a witness among three demos.

**Evidence.** The 100-lessons-per-band census produced 300 lessons and 1,200 rotations with zero ambiguity. Fixed-seed enumeration covered both declared schedule residues in all three bands: 6 lessons, 24 rotations, zero ambiguity.

**Failure mode / limit.** The exhaustive claim is only over the declared period at one fixed seed and the finite declared rival set. Random support is sampled, not mathematically exhausted.

## D6 — Preserve the Racket authority

**Prior choice.** The selected Racket rule already matched all canonical pairs and passed rule smoke.

**New choice.** Do not edit the canonical rule or selected authority. Pin `RULE_HASH = "c86a6d30fc9f"` in the generator and use a Python mirror only as supplementary test/probe logic.

**Alternatives considered.** No rule repair was justified; changing correct authority would add integration risk without addressing the generator defects.

**Evidence.** Rule smoke, Racket lint, and authority sync are green. The independent probe matches Racket 29/29; the retained shortcut fixture also matches real Racket.

**Failure mode / limit.** The Python mirror is not authority. Any future disagreement must be resolved in favor of the selected Racket source after investigating the mismatch.

## D7 — Retain independent probes and a minimal counterexample

**Prior choice.** No task-local tests, reusable reference probe, or retained counterexample existed.

**New choice.** Add focused tests, `workspace/reference_probe.py`, and `counterexamples/global_color_bbox.json`. The probe independently segments components and computes outputs rather than calling the generator’s prediction helper.

**Alternatives considered.** Relying only on the shared battery would miss task-specific teaching intent and would not preserve the exact canonical-fitting shortcut witness.

**Evidence.** The TDD record starts with 30 failures/13 passes, then 42/43 and finally a green focused suite. The counterexample test was observed red before its fixture existed and green afterward.

**Failure mode / limit.** Independent Python logic can share conceptual mistakes with the generator; real-Racket parity is therefore retained for canonical, generated, and counterexample inputs.
