# Working notes: bd6bfb1f0c20

## Current design

Version `2.0.0`; source SHA-256 `14245bd69e4764a5060836e1a03f960368f876248579f4ba9b81d369b719045d`; canonical rule hash `4f629ec7a9de`.

The intended rule is: find each nonzero four-connected monochrome object, compute its four-neighbor perimeter, sort by perimeter descending with color ascending as the deterministic tie-break, and output the object colors as one row.

Every generated input has three separated objects in distinct colors:

- L tetromino: area 4, perimeter 10;
- 2×2 square: area 4, perimeter 8;
- singleton: area 1, perimeter 4.

The square color is lower than the L color, so area-descending/color-ascending reverses the first two objects. Roles are placed in a noncanonical slot order, and objects are top-aligned within slots, so row-major position order also disagrees. These are structural invariants, not rejection-sampled tendencies.

## Reversed choices

The prior random 3–5-object sampler was replaced because it frequently made area order observationally equivalent to perimeter order. Lead: retained return `review-df404da564d3592d:v0001`; fresh before/TDD evidence reproduced the problem.

The prior broad control surface was removed because palette/texture/color-count controls were dead or inexact and dimension overrides were difficulty-local. Lead: retained return `review-ed3d39092c92c8c8:v0001`; fresh `lint`, `defect_lint`, and `override` failures reproduced the contract defects. Only exact observable `grid_h` 8..16 and `grid_w` 11..18 remain.

Random vertical offsets were removed after the semantic census found seed `146393197081358`, sample index `1981`, difficulty `easy`, where row-major order accidentally matched perimeter order. Horizontal offsets remain.

## Schedule and lesson contract

`LESSON_SCHEDULE_PERIOD = 4` with profiles `canonical_8x12`, `canonical_9x13`, `broad_compact`, and `broad_large`. Both canonical input dimensions occur in every ordinary eight-example window for every band.

Four demonstrations plus one query are used. Declared rivals are `area_order` and `position_order`; each generated input refutes both. The fixed-seed schedule receipt covers 12 lessons and 60 query rotations; the wider census covers 300 lessons and 1,500 rotations with no declared-rival ambiguity.

## Verification

- Final portable tests: 50/50 pass.
- Final battery: 12/12 stages green.
- Semantic census: 600/600 strict draws and 600/600 hits for each witness.
- Override census: 8,100 draws, zero findings or warnings.
- Racket source unchanged; authority sync and parity pass.

## Known limits and open work

The generated support uses one fixed semantic trio and exactly three objects. It does not teach perimeter ties, larger object counts, or a broad shape basis. The finite rival set is not proof against every shortcut. Add future families only with constructive per-example separation, focused regressions, required query rotations, and exact observable controls.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-ed3d39092c92c8c8:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `1c2a376f18950414e6abfcfb49b78f6c394e603fe2f1044d25083c9c5407ca03`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

One current decision covers both same-source findings: review-df404da564d3592d:v0001: Area-sort ambiguity on baseline1c2a376f1895 addressed by acceptedb1d21 return14245bd69e47: equal-area different-perimeter L/square objects, color-tie ordering counterexample and position schedule;300lessons/1500rotations,50 tests reported. No independent rerun. review-ed3d39092c92c8c8:v0001: Dead palette controls/missing rule pin on baseline1c2a376f1895 addressed by acceptedb1d21 return14245bd69e47: unsupported axes removed, only exact grid_h/grid_w, observer and RULE_HASH4f629ec7a9de;8100 reported override draws0findings and12/12 reported battery. Source-bound closure only.

### Assessment or prior finding

Source-bound supporting assessment from review-df404da564d3592d:v0001

## bd6bfb1f0c20

**Finding A-BD-1 — reproduced lesson ambiguity.** The canonical authority sorts component colors by four-neighbor perimeter descending, then color ascending. The generator claims four demonstrations cover an area-sorting rival, but a supported generated lesson at seed `0`, difficulty `medium`, sample indices `0..3` leaves that rival exactly consistent.

The four inputs were generated with the target generator SHA-256 `1c2a376f18950414e6abfcfb49b78f6c394e603fe2f1044d25083c9c5407ca03`. Canonical Racket rule hash `4f629ec7a9de` was applied with the supported `arcpuzzles apply` command. On all four demonstrations, the wrong rule “sort by area descending, then color ascending” produced exactly the same output as Racket. The complete inputs, outputs, rival outputs, hashes, command, and provenance are in `checks/audit/bd6bfb1f0c20/counterexample.json` and `racket.json`.

A deterministic independent scan used seed `0`, sample indices `0..399`, four consecutive demos per lesson, and 100 lessons per band. The area rival survived all demonstrations in:

- easy: 69/100 lessons, 364/400 matching pairs;
- medium: 20/100 lessons, 277/400 matching pairs;
- hard: 1/100 lessons, 133/400 matching pairs.

All 400 inputs were unique in each band. This scan reimplemented the published perimeter and area rankings in Python; the concrete seed-0 lesson was separately confirmed by Racket. Evidence: `checks/audit/scan.json` and `checks/audit/audit_probe.py`.

Secondary contract findings: lint fails for a missing `RULE_HASH`; defect lint flags four dead textures; the exact override gate reports declared values rejected by difficulty-local ranges and thousands of undeclared incompatibilities (`checks/audit/bd6bfb1f0c20/gate-*-after/`).

**Status:** reproduced generator/data-quality defect; no fix attempted.

Source-bound supporting assessment from review-ed3d39092c92c8c8:v0001

## bd6bfb1f0c20

**Finding A2 — reproduced dead exact controls.** The generator advertises `palette_kind`, `palette_size`, and `n_distinct_colors`, accepts overrides for them, but never reads those controls while drawing the grid. It also lacks a declared `RULE_HASH`.

At seed `17`, sample index `3`, difficulty `medium`, the following six requested settings all return the exact same self-check-clean grid (input SHA `84fa36b347709e4a29c4372e9bab379c25f5f7a2972c8bca351bbb015359560e`): `palette_kind=warm`, `palette_kind=cool`, `palette_size=2`, `palette_size=5`, `n_distinct_colors=2`, and `n_distinct_colors=5`. The observed nonzero colors are `[2,3,4,7,9]`, so several requested values are plainly not exact or observable.

I passed duplicate warm/cool inputs through the selected Racket authority; both outputs are identical, as expected for identical inputs, and executed rule hash `4f629ec7a9de` matches the catalog. `checks/audit/bd6bfb1f0c20/counterexample.json` records the exact overrides, source hashes, validator result, supported command, and output hashes.

**Suggested repair (not applied).** Remove dead controls or implement each with an `observe_overrides` contract; pin the canonical rule hash; then run lint, defect lint, profile floor, and the full override checker. The current `texture` helpful values appear to be a second alias path with the same observability problem.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-ed3d39092c92c8c8-v0001/audit_assets.json), manifest SHA-256 `e78c5fd82dfcf7a277412d185fbbd2778ce58ca08e8d034d397158201854a7ba`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `14245bd69e4764a5060836e1a03f960368f876248579f4ba9b81d369b719045d`.

# Decisions — bd6bfb1f0c20

## D1 — Replace the random motif sampler with a constructive witness family

**Prior choice.** Version 1.2.1 sampled several shapes and sizes, apparently to maximize surface diversity. The original rationale was not recorded, so this interpretation is inferred rather than claimed.

**Problem.** Perimeter and area were too correlated. A four-demo area sorter remained consistent in many retained lessons, and the fresh test-first suite reproduced the missing semantic contract.

**New choice.** Generate exactly an L tetromino, a 2×2 square, and a singleton. The L and square have equal area but different perimeters; assigning the smaller color to the square forces area-descending/color-ascending to disagree with perimeter order on every draw.

**Alternatives rejected.** Rejection-sample arbitrary shapes until area and perimeter differ; maintain a large catalog of hand-audited shapes. Both preserve more visual variety, but the first is harder to prove and debug, while the second adds unnecessary surface area before the basic teaching contract is reliable.

**Probe/evidence.** `checks/tdd-red/result.json`, `checks/after/checks/bd6bfb1f0c20_after_semantic_gate.json`, and `checks/lesson-census.summary.json`.

**Known limit.** The final distribution teaches one compact family of perimeter comparisons and does not exercise perimeter ties or many object counts.

## D2 — Make position-order disagreement structural

**Prior choice.** Objects had random offsets inside placement regions.

**Problem.** Even when role slots were selected in a noncanonical sequence, vertical jitter could make row-major order differ from slot order. The strict census found seed `146393197081358`, sample index `1981`, difficulty `easy`, where position order matched perimeter order.

**New choice.** Select a noncanonical role permutation for sorted slots and top-align each object inside its 3×3 slot; retain horizontal jitter only.

**Alternative rejected.** Compute realized object positions after painting and retry until they disagree. That would hide the invariant behind rejection behavior rather than make it true by construction.

**Probe/evidence.** `checks/tdd-red-position-census/result.json` and `checks/tdd-green-position-census/result.json`.

**Failure mode guarded.** Any future vertical jitter or slot-layout change must keep the pinned regression test and the 600-draw position witness green.

## D3 — Collapse the public control surface to observable exact axes

**Prior choice.** The baseline advertised palette, texture, color-count, object-count, and dimension controls; several were unused or only accepted inside difficulty-local ranges.

**New choice.** Expose only `grid_h` and `grid_w`, with strict full-domain validation and pixel-derived `observe_overrides`. Reject unknown keys and bool/float coercions.

**Alternatives rejected.** Implement all old axes; keep them as advisory metadata. Those options add complexity without improving the repaired teaching goal and would preserve ambiguity about exactness.

**Evidence.** Before `lint`, `defect_lint`, and `override` failures versus final 8,100-draw zero-finding override report at `checks/after/checks/bd6bfb1f0c20_after_override_results.json`.

## D4 — Schedule canonical shapes explicitly

**Prior choice.** Difficulty bands sampled different shape ranges and could omit canonical dimensions from ordinary lesson windows.

**New choice.** A period-four schedule emits 8×12, 9×13, compact broad, and large broad profiles. Every eight-example window contains both exact canonical shapes in every band.

**Alternative rejected.** Sample dimensions independently from one broad range. It has higher entropy but no deterministic canonical-profile floor.

**Evidence.** Focused schedule tests, final profile-floor report, and `checks/lesson-census-schedule.summary.json`.

## D5 — Declare the teaching hypothesis class

**New choice.** Add `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, and `lesson_identifiable` for area and position sorting. Keep `EXAMPLES_NEEDED = 4`; each example is independently discriminating, so every four-example lesson is redundant rather than fragile.

**Alternative rejected.** Rely only on aggregate output correctness. Correct labels do not establish that a lesson identifies the intended rule.

**Evidence.** Required-rotation semantic gate and both lesson censuses.

**Known limit.** The declarations are finite. Numeric-color heuristics, shape-specific memorization, and other undeclared programs remain possible.

## D6 — Keep the selected Racket authority unchanged

The canonical transformation and output labels were correct. The defect was in the generator and its contract, not the Racket rule. `RULE_HASH = "4f629ec7a9de"` now pins the existing authority; `authority_sync` and execution parity pass.

## D7 — Treat diversity as subordinate to semantic margin

The final generator intentionally sacrifices some shape diversity to guarantee that every input separates the two measured shortcuts. Current diversity remains nontrivial through dimensions, colors, L symmetries, horizontal offsets, and placement permutations, but future diversity additions should be constructive and test-first rather than random-first.
