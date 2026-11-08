# Current notes: `52d56c2a0191`

## Intended rule

Find color-2 components under 4-connectivity, retain the size of every component including duplicate sizes, sort ascending, and return the integers as a one-row grid. Canonical rule hash: `5c9566dd0981`; the selected Racket authority is unchanged.

## Current generator domain

Version `4.0.0` emits three to five red components of size `1..9`, at least two non-red distractor colors, and exactly one of the five canonical `(height, width, palette-count)` profiles. Its only public controls are exact `scene_profile` and `canvas_profile` values. A constructive 10×10 frame is flipped/translated inside the chosen canvas; generation checks that both controls can be reconstructed from the output grid.

The four semantic profiles are `canonical`, `repeated`, `diagonal`, and `large`. The default four-slot cycle is designed so any three profiles used as demonstrations distinguish the named rivals on the held-out fourth profile. `EXAMPLES_NEEDED = 3`.

## Reversed prior choices

The imported `3.0.1` generator exposed eight synthetic controls and allowed `texture="no_red"`; `self_check` accepted that scene even though the authority could not return a valid grid. Those controls were removed rather than patched individually. Missing red, unsupported semantic patterns, and noncanonical canvas/palette profiles now fail validation.

The first `4.0.0` draft used one fixed size signature per semantic profile. Lint correctly reported collapsed output diversity, so each profile now draws from a broad family of lawful size multisets. Difficulty-specific keyed RNG labels alter surface realization without changing exact profile semantics.

## Evidence and limits

Final generator SHA-256: `fb6ab5e45958a64fa7fad8ebe5ca2cfccc2601d135bd05893b7ead8ade96afee`. The full after battery is 12/12 green, portable tests are 80/80, and a 300-lesson census checked 1,200 pairs and all 1,200 query rotations with no ambiguity, hook warning, or scoring error against the declared rivals.

The strongest canonical-fitting rival is 8-connected red-component sizing. A Racket-checked exact disagreement is retained at `counterexamples/review-4292d812db8d55cb-v0001/diagonal-connectivity.json`.

Known limit: the identifiability result is finite and restricted to declared rivals and the selected canonical-profile manifold. It is not a proof of unique induction against every possible rule, nor does the generator claim arbitrary canvas dimensions or palettes.
## Current reviewer considerations

Source SHA-256: `fb6ab5e45958a64fa7fad8ebe5ca2cfccc2601d135bd05893b7ead8ade96afee`.

# Decisions for `52d56c2a0191`

## D1 — Replace the baseline control surface rather than patch individual axes

**Prior choice:** version `3.0.1` exposed eight synthetic controls, including `texture="no_red"`. Their original rationale is not recorded in the current notes. Several controls were not exact observable properties, and some combinations left the authority's executable domain.

**New choice:** expose only `scene_profile` and `canvas_profile`. Both are finite, semantically meaningful, reconstructible from the emitted grid, and tested across their complete 4×5 cross-product in easy, medium, and hard bands.

**Alternatives considered:** retain all old names and add incompatibility declarations; or keep free-form height/width/palette controls. The first preserves a misleading API; the second admits many off-canonical combinations and makes exact palette support fragile. The selected interface is smaller but truthful.

**Failure modes and limits:** the sampler deliberately does not claim arbitrary canvas dimensions or arbitrary palettes. Adding a new profile requires a constructive layout and round-trip observation test.

## D2 — Require selector-bearing red scenes

**Prior choice:** `no_red` was a generated texture and `self_check` accepted it.

**New choice:** every lawful scene contains three to five color-2 components, and `self_check` rejects missing red, fewer than three red components, malformed palette profiles, and unsupported semantic profiles.

**Reason:** the unchanged Racket rule selects red components and cannot return a valid output when none exist. The prior audit and before battery established a validator/authority mismatch, not merely an aesthetic weakness.

**Alternative rejected:** define the no-red answer as an empty row. That would require changing the canonical authority and task domain without canonical evidence.

## D3 — Preserve exact canonical canvas/palette support

**Choice:** use exactly the five `(height, width, palette-count)` profiles observed in canonical data: `(10,12,7)`, `(10,13,5)`, `(11,10,4)`, `(13,11,5)`, and `(13,13,5)`.

**Construction:** build inside a 10×10 local frame, then flip and translate the complete frame inside the selected canvas. Distractor colors are distinct and their count is chosen so the final palette cardinality is exact.

**Probe:** all 60 `scene_profile × canvas_profile × difficulty` combinations round-trip through `observe_overrides`; the after override and profile-floor stages pass.

**Limit:** this intentionally narrows generation to the canonical shape/palette manifold. It does not assert that the mathematical rule would fail on other ARC-sized canvases.

## D4 — Teach the strongest canonical-fitting rivals directly

The canonical pairs fit all three of these wrong rules:

1. deduplicate repeated red-component sizes;
2. merge diagonally touching red cells using 8-connectivity;
3. cap all sizes at five, the largest size seen canonically.

**Choice:** a four-slot semantic schedule contains a distinct-size canonical scene, a repeated-size scene, a diagonal-contact scene, and a large-component scene. All scenes also contain non-red distractors, ruling out counting every colored component.

**Why four profiles:** three demonstrations must distinguish every named rival regardless of which of the four profiles is held out as query. Direct cyclic-start and all-query-position tests verify that property.

**Limit:** `lesson_identifiable` is a finite named-rival check. It does not claim universal rule uniqueness.

## D5 — Use guaranteed construction, not rejection sampling

**Choice:** connected components are prefixes of fixed connected paths in separated slots. Diagonal witnesses occupy reserved cells. All placements happen before any result is returned, and construction is checked against `observe_overrides`.

**Alternative rejected:** randomly grow blobs and retry until enough fit. That can bias requested profiles, silently drop late components on small canvases, and make exact overrides probabilistic.

**Failure mode addressed:** slot capacity is explicit. Sizes above five are assigned only to 3×3-capacity slots; canonical/repeated sizes stay at most five.

## D6 — Broaden outputs after the lint diversity finding

**Initial repaired choice:** one fixed component-size tuple per scene profile. It passed semantic tests but created only four possible outputs.

**Reversal:** enumerate broad lawful multisets for each profile and draw deterministically from them. The canonical profile spans distinct subsets of `1..5`; repeated spans repeated four-element multisets; diagonal and large combine singleton diagonal witnesses with varied small and `6..9` sizes.

**Evidence:** the regression uses the same 24×6 lattice as lint and requires at least 60 distinct outputs. Final lint and diversity stages pass.

## D7 — Let difficulty alter surface form, not task semantics

**Choice:** difficulty is included in keyed RNG labels for size selection, component assignment, layout, and distractor palette. Exact requested profiles and witness obligations remain unchanged.

**Reason:** the previous first repair produced byte-identical grids across bands for the same seed/index. The current test requires three distinct grids while requiring identical observed profiles.

**Limit:** difficulty does not currently impose a formal monotone reasoning-complexity scale; it supplies reproducible surface variation. No stronger claim is made.

## D8 — Keep the Racket authority unchanged

The canonical rule hash is pinned as `5c9566dd0981`. A Python `rule_mirror` exists only for tests, witnesses, and authoring diagnostics. Racket remained the label authority for the battery, lesson census, and retained exact counterexample.

Changing the authority was rejected because the defect was entirely in the generated input domain and curriculum, and all canonical outputs already matched the intended 4-connected red-size rule.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-d956010e627d79d5:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `2ffebf69fe62f090dbe467b8bf098e34559369c69961cb895ae5d606dcfabff0`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Current unchanged source rejects texture=no_red and validator rejects the retained no-red input, independently rechecked in review-89effc2f42a416a4 checks/audit/52d56c2a0191/inherited_recheck.json. Resolve only no_red; new frequency-selector gap stays unresolved. Old source 2ffebf69fe62f090dbe467b8bf098e34559369c69961cb895ae5d606dcfabff0.

### Assessment or prior finding

## 52d56c2a0191

**Classification: reproduced defect. Target was not modified.**

I checked the public texture controls and validator/authority agreement for generator SHA-256 `2ffebf69fe62f090dbe467b8bf098e34559369c69961cb895ae5d606dcfabff0`.

Exact reproducer: `generate(123, 0, texture="no_red")` emits an 11×11 grid with nine nonzero distractor cells and zero red cells. The target's `self_check` accepts it (`[]`), so the input belongs to the generator's advertised public domain as currently implemented. The selected rule hash `5c9566dd0981` cannot produce a valid ARC grid without its red selector: public `arcpuzzles apply` exits 1 and reports `rule returned a value that is not a rectangular 0-9 grid`.

This is an authority-domain/validator mismatch. The validator should require the selector, or `no_red` should be removed/declared incompatible unless the rule/domain is deliberately redesigned.

Evidence: `checks/audit/52d56c2a0191/finding.json`, `input.json`, `generator_observation.json`, `racket.json`, `apply.log`, and `apply.exit`.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-d956010e627d79d5-v0001/audit_assets.json), manifest SHA-256 `611387a7b4773fc931f853d93f9ad8e96cc856df44327f6f2e2f40d5c24d3f94`.
<!-- arcpuzzles-current-audit-assessment:end -->
