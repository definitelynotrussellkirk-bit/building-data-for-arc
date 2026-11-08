# Current generator decisions: f68fe53c1702, v3.0.0

## Intended rule and domain

Canonical Racket authority `ab8196a7d821` is unchanged: use every nonzero cell to determine the bounding box, then draw its outline in the single marker color on a fresh same-size zero grid. Strictly interior markers disappear. The ordinary generator domain is a rectangular native-integer grid with height 4..24, width 5..24, one foreground color in 1..9, 2..7 distinct markers, and bbox span at least 3x3. Multicolor, empty, singleton, aligned, narrow-bbox and dense inputs remain outside this sampler, even where the Racket program has a defined result.

`strict_canonical_like` deliberately recognizes the literal three-corner construction. Distributed extrema are reference-lawful teaching extensions, not mislabeled as literal canonical layouts. All four canonical train inputs and the labeled test input remain accepted.

## Reversals and rationale

- **Inert controls → four exact controls.** v2 ignored size, color and count requests and accepted unknown axes. v3 records and honors `grid_h`, `grid_w`, `color`, and `num_cells` in every band. Non-integer values and out-of-range requests fail; `None` retains the shared no-override convention. The previously inert or singleton `palette_kind`, `texture`, `palette_size`, `n_distinct_colors`, `position_bias`, and `bbox_aspect` declarations are retired and rejected explicitly. This interface change is reflected in the major version bump.
- **Always NW+SE → canonical and distributed extrema.** v2 always occupied one full bbox diagonal, making the Euclidean-farthest-pair shortcut answer-equivalent on every normal draw. v3 varies the missing canonical corner and uses rich layouts with at most one occupied corner, plus a strictly interior marker. A rich layout refutes both farthest-pair framing and preserving input markers while adding the frame.
- **Independent sparse draws → period-3 teaching profiles.** Default indices repeat canonical-corners, rich, rich. A four-consecutive-index bundle therefore has at least two rich examples; every one-pair holdout leaves a rich demonstration. Default lessons use three demonstrations. Geometry, color, placement, aspect ratio and border contact still vary with the seed and full sample index. Exact count-2/3 overrides use lawful corner constructions; their queries are answer-equivalent under the declared rivals. Arbitrary sparse index selections do not inherit the schedule guarantee.
- **Hard-only large canvases → canonical anchors in every band.** The canonical profile uses one of the five observed canvas shapes with a freely sampled nonzero color. Rich profiles retain easy/medium/hard size ranges. Size overrides take priority, including the 4x5 boundary. Palette size is an invariant rather than a fictitious degree of freedom.
- **Placement collisions → constructive distinct placement.** Feasible bbox spans are selected before placement; rich layouts reserve corner capacity, explicitly establish every extreme, and add distinct markers without clipping requests or capped rejection loops.
- **Unsynchronized selected comments → exact active authority text.** The selected base solution's `target_code` had two extra comments, one naming the wrong top-edge row. Those comments were removed to match its existing `raw_code` and the canonical program. No executable Racket expression or canonical row changed.

## Evidence and current audit status

The source-bound lead was audit `review-fc5b1524baa2134f:v0001`, A1, on generator SHA256 `064a407dd0a21a9b320b226f301bf5af7d2e733e6dc0a0818d17beed6e235bf2`. Intake explicitly resolved its override and validation defects against the accepted v3 source `90e4a1ca55d14dc1c78d2e3c5a546d6969fed41e604415df349d01b53a572c30`, with the 47-case regression and 12,600-draw report as reviewer-reported evidence. The task-local regressions and distributed-extrema witness retain the useful repair evidence; unrelated audits remain separate.

Final generator SHA256: `90e4a1ca55d14dc1c78d2e3c5a546d6969fed41e604415df349d01b53a572c30`.
The review's `checks/after/` records all 12 stages passing, including required query rotations; `checks/task-tests/` records 47 passed and zero skipped. The exact override matrix accepted 12,600/12,600 draws with zero findings. `checks/lesson-census.json` contains 300 production lessons, 1,200 holdouts and 1,198 unique inputs, with no measured ambiguity against the two declared rivals. These are finite source-bound checks, not universal induction or model-training admission.

`counterexamples/distributed-extrema.json` contains a generated 4x5 witness (seed 117, sample index 1, easy, color 2, count 4), supported Racket output, and both rival predictions. `workspace/reproduce_witness.py` replays it. `workspace/probe_geometry.py` independently checks count/extrema/interior geometry over the declared bbox ranges. New regressions live in `tests/test_bbox_contract.py`; the frozen legacy fixture was not changed.

## Remaining limits

No unresolved defect was found in the repaired sampler within the measured scope. The four-point rich construction and three-corner profile are purposeful teaching components; they do not cover every lawful sparse point set or every possible rival. Difficulty changes spatial scale more than conceptual depth. Keep the single-operation bbox task separate from multi-rule or task-defined-symbol curricula. Maintainer integration and explicit audit-status updates remain distinct from these reviewer checks.
## Current reviewer considerations

Source SHA-256: `90e4a1ca55d14dc1c78d2e3c5a546d6969fed41e604415df349d01b53a572c30`.

# Decisions for review-09078f3c08634910

## Goal and authority

Improve the selected generator's controllability and teaching value while preserving the canonical bbox-outline rule. The assignment, both random audits, and the blind target remain unchanged. The scope is one generator and its allowed selected authority record; audit sources and shared implementations are findings-only.

The executable canonical rule explicitly takes all nonzero cells, chooses their shared color, and paints the bbox perimeter onto a new empty grid. The original written canonical task has three corners; the prior generator already extended that domain to two through seven markers. V3 keeps those bounded controls and adds useful lawful marker layouts. It does not invent a new composed transformation.

## R1 — real, observable controls

**Prior choice:** ten declarations advertised size, palette, placement and texture variation, but the implementation directly used one layout RNG. Except for invalid degenerate textures, it did not consult overrides. The author's original rationale for exposing those inert names is unknown. The imported current notes were empty.

**Choice:** keep exactly `grid_h=4..24`, `grid_w=5..24`, `color=1..9`, and `num_cells=2..7`. Every one is directly observable from the returned grid and uses keyed context draws. Validate unknown names, true integer types and bounds before any misleading success. `None` remains the framework's no-override convention.

**Rejected alternative:** implementing named warm/cool/rainbow palette modes alongside a single exact color. Those overlapping modes would add aliases and compatibility conditions without adding an independent task-relevant degree of freedom. Palette size, monochromaticity and real-rectangle extent are invariants, not tunable singleton axes. Retire all six old redundant declarations, with explicit errors rather than silent fallbacks. V3's major version records this API change.

**Evidence:** the existing source-bound A1 audit was freshly reproduced. New regressions initially yielded 42 failures/5 passes; v3 yields 47 passes. The final override matrix covers 140 cases per band with 30 seeds, all three bands: 12,600 accepted draws, zero findings/rejections/errors. It probes both size endpoints, every color and every count. Separate boundary tests include jointly requested minimum canvas/maximum count, invalid types and out-of-range values.

## R2 — distributed extrema and interior erasure

**Prior choice:** always place NW and SE corners, optionally add other corners and randomly sampled markers. This made farthest-pair framing an exact shortcut on the entire default support; random duplicate placements also made `num_cells` an unreliable description.

**Choice:** use three-corner inputs as a canonical component and use rich configurations with at most one corner, distributed row/column extrema and at least one strict interior marker. Every rich configuration refutes taking any single pair's bbox, hence the farthest-pair rival, and refutes adding the frame while preserving all input marks. Count four can realize this using one corner, two side extrema and one interior point. Counts five through seven also support four independent noncorner side extrema plus interior cells. Random row/column reflections, positions and extra distinct cells broaden these constructions.

**Rejected alternatives:** retaining the mandatory diagonal, merely changing colors/sizes, or only adding more interior points. None would refute the geometric shortcut. Generating only rich examples would remove explicit canonical construction support; using a pure random mixture could leave a complete lesson without the distinction it needs.

**Placement:** choose a feasible bbox span first. Rich spans reserve four corners worth of capacity, sufficient for both rich constructions. Markers are sampled without replacement from legal unused positions. This avoids ignored requests, duplicate-count collapse, truncation and retry-dependent success. The existing height-4 boundary is retained; padded canonical placement is not imposed where impossible. All grids keep a nonzero foreground distinct from zero background.

**Witness:** `counterexamples/distributed-extrema.json` binds a generated 4x5 example to seed 117, index 1, easy, height 4, width 5, color 2 and count 4. Both rivals fit all five canonical pairs and disagree with its actual Racket output. This is a generated witness, not just an accepted hand-crafted grid.

## Teaching schedule, ordering and overrides

Default semantic profiles repeat `canonical_corners, distributed_extrema, distributed_extrema` with period three. The default component counts are three markers for canonical profiles and four through seven for rich profiles. The full seed and sample index continue to drive geometry; period three repeats semantic roles, not exact images.

Three demonstrations plus one query from four consecutive sample indices have at least two rich examples. Any one-of-four holdout therefore leaves a rich demonstration. The public hook checks actual materialized labels and rival predictions, so its evidence is not inferred only from requested indices. It reports a defect only when a rival fits all demonstrations and changes the query answer; a rival that agrees on the query is not an ambiguity.

Count-two and count-three overrides intentionally use corner constructions. Those queries are answer-equivalent for the two declared rivals and need no artificial witness requirement. Other exact counts override the curriculum counts without changing their requested values. The default schedule guarantee does not extend to arbitrarily chosen sparse indices or undeclared rivals.

The shared census used three demonstrations, one query, consecutive requested starts 0..99, SHA256-derived per-band/per-start seeds, and every one-pair query rotation. All 300 lessons/1,200 rotations completed without measured ambiguity or errors. Its residue-reporting modulus defaults to six; that is not a claim that the generator's semantic period changed from three. The focused tests additionally check every holdout for twelve consecutive starts at four seeds per band. Those windows are overlapping evidence, not independent sample counts.

## Canonical anchoring, difficulty and validation

The canonical component samples the five canonical canvas shapes independently of foreground color; it does not replay canonical grids or tie color to a shape. Rich easy/medium/hard ranges retain the former spatial-scale progression. Overrides take precedence in every band. This repairs the old zero hard-band profile support while retaining broad geometry.

`self_check` recognizes the documented bounded sampler domain, including lawful distributed-extrema extensions. It rejects malformed shapes, boolean/fractional/out-of-range colors, mixed foreground colors, dense marker counts and degenerate bboxes. `strict_canonical_like` is narrower: exactly three actual bbox corners. Measured strict support is 209/600, not an inflated 100%; all five canonical inputs pass both checks. Exact profile support is 25/60 overall (7/20 easy, 9/20 medium, 9/20 hard).

Empty, singleton, aligned, one/two-row bboxes, multicolor and dense inputs remain excluded. Although the Racket program has behavior on some of them, adding those regimes would change the lesson vocabulary and controls without resolving this assignment's central defect.

## R3 — active authority synchronization

The canonical row and the selected solution's `raw_code` already matched. Its active `target_code` differed only by two comments, including an incorrect top-edge annotation. Exact authority synchronization was failing even though sampled behavior matched. Removing only those comments preserves every executable expression and the canonical hash while making both active authority texts equal. The final battery's authority and defect-lint stages pass. The returned Racket component is required to carry this cosmetic synchronization; no canonical JSONL row changed.

## Tests, useful tools and rejected extra work

New tests are portable task-local regressions, not edits to frozen fixtures. `probe_geometry.py` retains an independent count/extrema/interior check over all declared rich bbox dimensions and counts at four seeds (7,736 cases), 40 feasibility boundaries and 72 public boundary draws. `reproduce_witness.py` supplies a small reproducible public-Racket witness with dynamically enumerated canonical shortcuts. These are the two reusable tools added for future agents; the existing shared census and check runner already handle lesson scoring and command receipts, so no duplicate general framework was added.

An initial apply-patch invocation used an unsupported delete-plus-add form for the same path; it made no change and was retried as an update. A verification helper for audit 5d59b75cb58e initially expected the wrong apply-result key; its failed log remains, and the corrected helper passed. Neither was a hidden generator revision or a fabricated solve failure.

The broad root suite was stopped after an unrelated historical snapshot failure. A focused replay of the same test on an untouched extraction reproduces the same pair-hash mismatch. Changing that fixture or shared sampler is outside this selected repair; the issue is reported as T1/F2 rather than made green by changing an expectation.

## Audit follow-up and remaining scope

366cda05b486 has a concrete default-lesson ambiguity: the largest contact cluster happens to be the blue-selected cluster in all demos but not in the query. Retain the lesson and add a proper teaching witness/competitor in a future assigned repair. 5d59b75cb58e has a low-severity invalid-override coercion defect; its 39 audited Racket labels are correct. Both task sources remain unchanged.

For the main task, the inherited A1 audit's reproduced findings are addressed by v3; an explicit maintainer audit-status resolution is proposed using the final source and tests. Its packet index and prior assets were not rewritten, so source acceptance cannot silently erase audit state.

This remains a single geometric operation. Larger canvases do not make it a multi-rule, sequential-state, contextual-gating or task-defined-symbol task. No corpus-wide data-quality or model-performance claim follows from one repaired generator and two audits. Source approval, hidden-query scoring and training admission remain maintainer decisions.
