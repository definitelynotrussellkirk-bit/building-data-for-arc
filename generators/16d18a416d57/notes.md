# Working notes: 16d18a416d57

## Intended rule and authority

The canonical Racket authority is unchanged: among 4-connected blue (`1`) components, recolor the uniquely largest component orange (`7`) and preserve all other cells. `RULE_HASH = 54df007aec53` pins that authority. Inputs generated here use only background `0` and blue `1`, have 2–4 components, and keep distinct components separated even diagonally.

## Review review-273a9f905031501d

Pinned baseline generator SHA-256: `a9d58e02a5aaf174348b783c0059d1109050b08727e8d0633494ff06d0410ea0`.
Final generator SHA-256: `06cacd590950edb5f84ab7e8d917aaca93bc915e1fea9ec99d94b56f06ca6bdf` (`VERSION = 2.1.0`).

Prior return `review-a0fe7111a89db996:v0001` was used only as a lead. The current baseline was remeasured independently. It advertised dead palette/texture controls, accepted unknown keys, exposed invalid negative textures as ordinary controls, rejected many declared dimensions, and omitted the canonical `(2,4,5)` component profile. The before battery recorded 7 green, 2 advisory, and 3 failed stages; the override matrix retained 11,269 findings across 37,800 draws.

### Reversed choices

- **Prior:** broad `texture`, palette, motif-count, and size controls whose values were dead, incompatible, or invalid. **Now:** only three exact observable controls: `grid_h` in 8–12, `grid_w` in 10–14, and one named component-size profile. Unknown, retired, mistyped, out-of-range, and `None` overrides fail explicitly.
- **Prior:** ordinary draws did not cover the canonical size-2 minority. **Now:** `canonical_245` and `canonical_345` reproduce canonical support; `varied_246`, `two_35`, and `four_2346` provide lawful noncanonical support.
- **Intermediate:** a three-phase schedule always used a size-5 winner and randomized within-zone translation. **Now:** a four-phase schedule alternates winner sizes 5 and 6, places the winner first/middle/last/middle in row-major discovery order, and anchors normalized shapes at zone origins so query rotation cannot silently change that order.
- **Intermediate:** a declared 50% strict floor equaled the theoretical periodic rate and failed a finite random sample at 45.3%. **Now:** `MIN_STRICT_FRAC = 0.40`, leaving margin below the deterministic 50% schedule expectation without changing the schedule itself.

### Teaching contract

Executable rivals cover first component, last component, smallest component, largest bounding-box area, and a fixed size-5 target. Schedule phases 1 and 2 include a size-4 component whose bounding box ties the true winner's area; phases 1 and 3 use size-6 winners. `lesson_identifiable` rejects any declared rival that fits all demonstrations but changes the query.

Minimal retained counterexamples are under `counterexamples/review-273a9f905031501d/`:

- `baseline_invalid_override.json`: advertised `texture=no_motifs` generated outside the grammar.
- `canonical_size_two_gap.json`: exact canonical `(2,4,5)` support absent from the old defaults.
- `rotation_order_ambiguity.json`: an intermediate lesson whose translated shapes let first-component and bounding-box rivals survive a query rotation.
- `fixed_size_five_shortcut.json`: a lawful size-6 winner that refutes “always recolor the size-5 object.”

### Final evidence

The final source passed all 12 native battery stages, 89 focused portable tests, a required-rotation semantic gate, 300 production lessons with 1,200 held-out query rotations, and all 12 fixed-seed schedule starts with 48 rotations. All tested lessons were materialized and scored without ambiguity, warnings, or errors against the five declared rivals. See `checks/after-final-v3/`, `checks/task-tests-final-v3/`, `checks/required-rotations-final-v3/`, `checks/lesson-census-final-v2.json`, and `checks/schedule-census-final-v2.json` in the return.

## Known limits

The finite lesson results establish only the tested generator bytes, seeds, bands, assembly policy, and declared rivals. Fixed-seed schedule enumeration covers every declared residue at seed 0, not every seed. Shape support is intentionally bounded to connected size-2 through size-6 variants fitting 3×3 placement zones; this is sufficient for the selected curriculum but does not exhaust every authority-lawful blue object. The generator remains catalog-unapproved until maintainer intake.
## Current reviewer considerations

Source SHA-256: `06cacd590950edb5f84ab7e8d917aaca93bc915e1fea9ec99d94b56f06ca6bdf`.

# Decisions for `16d18a416d57`

## D1 — Keep the authority fixed

**Choice.** Preserve the canonical Racket rule and pin `RULE_HASH = 54df007aec53`.

**Why.** Canonical examples and the authority consistently express “recolor the uniquely largest blue 4-connected component.” The measured defects were all in input generation, metadata, validation, and teaching support; changing the target rule would have hidden those defects.

**Probe.** Canonical pairs were checked by an independent Python component oracle, then native `rule_smoke` and `authority_sync`. Final result: both green.

**Failure mode avoided.** A generator repair must not redefine the puzzle to fit its current restricted support.

## D2 — Expose only exact, observable axes

**Choice.** Keep `grid_h`, `grid_w`, and `component_profile`; remove palette, texture, motif-count, and related pseudo-controls. Reject unknown keys, `None`, wrong types, invalid enum values, and out-of-range dimensions.

**Original rationale.** Unknown. The pinned source advertised many values but several were singleton, ignored, incompatible with band-local bounds, or deliberate invalid fixtures mixed into ordinary support.

**Alternatives rejected.** Declaring thousands of incompatibility combinations would preserve a confusing public contract. Keeping “negative textures” as ordinary values would continue producing grids that fail `self_check` or have no valid authority target. Exact named profiles make every value directly recoverable through `observe_overrides`.

**Probe.** One value per axis plus cross-band combinations and unknown-key tests. Baseline red: 33/63 failures. Final: every advertised request round-trips in every band, and override battery is green.

## D3 — Model component support as named size profiles

**Choice.** Profiles are `canonical_245`, `canonical_345`, `varied_246`, `two_35`, and `four_2346`.

**Why.** The semantic object is component-size ranking, so profiles expose meaningful input structure rather than unrelated style labels. The two canonical profiles reproduce exact canonical size support, including the previously absent size-2 minority. The others provide lawful diversity and size-6 winners without changing the rule.

**Alternatives rejected.** Independent arbitrary size/count axes would need a larger compatibility surface and could create ties. A single hard-coded profile would be valid but too easy to solve by fixed size.

**Limits.** Sizes are bounded to 2–6 and shapes fit 3×3 zones. Authority-lawful larger objects are not claimed as generator support.

## D4 — Use a deterministic four-phase lesson schedule

**Choice.** Defaults cycle `canonical_245`, `varied_246`, `canonical_345`, `varied_246`. Winner discovery rank is first, middle, last, middle. Winner size is 5, 6, 5, 6. Shapes are anchored at the selected zone origin.

**Why.** Three demonstrations must refute first/last and fixed-size shortcuts regardless of which of the four pairs becomes the query. The four phases supply both winner sizes and all relevant discovery positions. Anchoring preserves row-major order; random within-zone translation previously swapped components and caused 15 ambiguous rotations in 1,200.

**Alternatives rejected.** The intermediate three-phase cycle had all size-5 winners. Random translations added visual variation but invalidated the advertised positional curriculum. Shape variation through rotations/reflections already supplies diversity without moving a component across its discovery boundary.

**Probe.** Exhaustive windows starting at six consecutive indices in every band, then 300 production lessons with every query held out, plus all four schedule residues at fixed seed 0.

## D5 — Include explicit semantic rivals and witnesses

**Choice.** Declare executable rivals for first, last, smallest, largest bounding-box area, and fixed size five. Include witnesses for each.

**Why.** Correct per-grid labels do not guarantee teachable lessons. Named rivals make the intended distinctions executable and let the lesson census report which hypothesis survives.

**Bounding-box construction.** In phases 1 and 2, the size-4 component and true winner are each selected from shapes with bounding-box area six. The rival's deterministic tie behavior selects the smaller component, while the authority uses cell count.

**Fixed-size construction.** Phases 1 and 3 have size-6 winners and no size-5 component, so a size-5 rival returns identity and is refuted.

**Limits.** The declared set is deliberately plausible and small; passing it is not proof against every program consistent with finite examples.

## D6 — Separate grammar validity from canonical similarity

**Choice.** `self_check` accepts every declared lawful profile; `strict_canonical_like` accepts only canonical dimensions and canonical component profiles. `MIN_STRICT_FRAC = 0.40` is a finite-sample floor below the deterministic 50% default expectation.

**Why.** Noncanonical but authority-lawful counterexamples are necessary for teaching, while canonical support still needs explicit measurement. Setting the floor equal to the expected 0.50 made random-index sampling brittle: one native run observed 272/600 = 45.3% despite the exact periodic schedule.

**Alternative rejected.** Raising the observed fraction by removing size-6 lessons would reopen the fixed-size shortcut. Lowering the floor without documenting the schedule would hide a distribution regression; the focused test asserts both the 0.40 declaration and the 2/4 canonical schedule.

## D7 — Retain failures and bind the final solve to final bytes

**Choice.** Keep all decisive red evidence: baseline task tests, rotation failure, fixed-size failure, and strict-floor failure. Preserve the intermediate solve under `checks/prior-solve-7dc6adc14481/`, then prepare a new solve after the final SHA was fixed.

**Why.** The failures identify what each change actually repaired, and a copied old solve would not establish behavior for the final generator.

## Final measured scope

Final source SHA-256: `06cacd590950edb5f84ab7e8d917aaca93bc915e1fea9ec99d94b56f06ca6bdf`.

- Native battery: 12/12 green.
- Focused portable tests: 89/89 green.
- Required-rotation semantic smoke: passed.
- Random production census: 300 four-pair lessons, 1,200 held-out rotations, 1,093 unique inputs, zero ambiguity/errors against the declared rivals.
- Schedule census: all four residues × three bands at seed 0, 12 lessons and 48 rotations, zero ambiguity/errors.

These are finite, source-bound measurements. They do not certify all seeds, all authority-lawful objects, or undeclared hypotheses.

## D8 — Add an opt-in size-keyed partner family without changing authority

**Choice.** Preserve the exact canonical program as the default `mode=canonical`. Add only an opt-in `mode=size_keyed_partner`: identify the unique largest blue component, measure its size `s` in `{5,6,7}`, paint it orange, then paint the unique blue component of size `s-3` red.

**Why.** The new-policy MAIN requires a real A → input-dependent intermediate → B dependency. Every generated input also contains blue components of sizes 2, 3, and 4, so B cannot be fixed in advance: `s=5` selects size 2, `s=6` selects size 3, and `s=7` selects size 4. The canonical generator and accepted rule remain untouched.

**Teaching and edge checks.** Demonstrations 1 and 2 use largest sizes 5 and 7, so the minimum two-demo lesson already distinguishes both settings and defeats every fixed partner choice. A bounded audit over seeds 0 and 17, demo counts 2–6, both settings, and seven plausible shortcuts found no demo-fitting rival that changed a query. Invalid settings/counts/types are rejected, all inputs within an episode are distinct, and the four-query set includes a nontrivial 30×30 boundary/distractor case.

**Native evidence.** Qualification passed for both settings across four jobs. Protected Racket reproduced 40 audit labels. A source-bound three-case causal witness covered `s=5,6,7`; six protected-Racket replay evaluations showed that a wrong intermediate changes the final output each time. Public-only serialization passed for both settings. Fresh staged task tests passed 128/128.

**Limits and next action.** These are finite, source-bound checks against declared rivals, not universal uniqueness or measured training gain. Owner integration must replay the witness, rerun native qualification, and explicitly accept the exact integrated source; no training admission is claimed here.

