# Current account: `57df2ac388cd`

Final selected generator version: `4.0.0`
Final `generator.py` SHA-256: `0e2a5cebd5fd2a44b33850eac511d8745d3b16832d467734971f31024c5f818b`
Canonical rule hash: `a668b763669f` (unchanged)

## Intended rule

Find the first two nonzero monochrome 4-connected objects in row-major scan order. Crop each to its own bounding box, align both crops at their top-left, and output their normalized union. Shared cells become color 8; cells unique to the first object keep its color; cells unique to the second keep its color.

## Reversed baseline decisions

- **Prior:** any normalized overlap was enough. **Now:** every lawful example has overlap, first-only, and second-only cells. **Reason:** the old subset relation omitted a semantic branch; see `counterexamples/normalized_subset.json` and focused tests.
- **Prior:** texture and motif controls were advertised but inert, and negative fixtures appeared lawful. **Now:** exact observable controls are `grid_h`, `grid_w`, `motif_a_cells`, `motif_b_cells`, and four helpful textures; unknown keys fail, while degenerates are diagnostic-only.
- **Prior:** no pinned authority hash or executable semantic contract. **Now:** `RULE_HASH` is pinned and named witnesses/rivals cover each output branch plus lesson identifiability.

## Distribution choices

Lawful grids are 9–16 rows by 9–18 columns and contain exactly two separated monochrome motifs, each 3–6 cells. Shapes are sampled from the complete fixed 4-connected polyomino support through size 6, with a deterministic total placement fallback. A 45% prior emits the canonical 9×9 scale in every band. Textures map to fixed pairs: default `(2,3)`, warm `(4,7)`, cool `(1,5)`, varied `(6,9)`.

Each lesson uses 3 demonstrations. Every pair individually exercises all three branches, and `paint_overlap_first`, `erase_first_only`, and `erase_second_only` are declared as semantic, lesson, and canonical-shortcut rivals.

## Final evidence

- Twelve-stage after battery: 12/12 green, `checks/after/checks/57df2ac388cd_after_battery_summary.json`.
- Focused task tests: 41/41 passed, `checks/task-tests-portable-final/result.json`.
- Fresh exact-patch replay: isolated Git root, apply-check/apply exit 0, matching generator hash, and 41/41 tests, `checks/fresh-replay/final/replay.json`.
- Semantic gate: 600/600 strict draws; all named branch claims 60/60, `checks/after/checks/57df2ac388cd_after_semantic_gate.json`.
- Lesson census: 300 lessons, 1,200 unique inputs, production ambiguity 0/300, required query-rotation ambiguity 0/1,200 against declared rivals, `checks/lesson-census.json`.
- Post-repair solve used the same final generator hash and passed all 3 visible demonstrations on revision 1, `solve/summary.json`.

## Known limits / open questions

This is finite declared-rival evidence, not universal identifiability. The generator intentionally excludes touching source objects, more than two objects, shapes outside 3–6 cells, and arbitrary palette permutations. The fixed texture palettes improve exact controllability but do not train color-role interchangeability. No canonical Racket change is proposed.
## Current reviewer considerations

Source SHA-256: `0e2a5cebd5fd2a44b33850eac511d8745d3b16832d467734971f31024c5f818b`.

# Decisions for `57df2ac388cd`

Final generator SHA-256: `0e2a5cebd5fd2a44b33850eac511d8745d3b16832d467734971f31024c5f818b`
Canonical rule hash: `a668b763669f` (unchanged)

## D1 / R1 — Require all three normalized overlay branches

**Prior choice.** The baseline accepted any two normalized shapes with at least one shared cell. That allowed containment/equality relations, so an otherwise lawful pair could omit first-only or second-only support.

**New choice.** Every generated shape pair must satisfy all of: nonempty overlap, nonempty first-minus-second, and nonempty second-minus-first. `self_check` enforces the same contract.

**Why.** The output rule has three distinct semantic cases. A small model can fit a shortcut when a labelled example never exercises one case, even though its label is correct. The minimal retained counterexample is [`repo/generators/57df2ac388cd/counterexamples/normalized_subset.json`](repo/generators/57df2ac388cd/counterexamples/normalized_subset.json); it has no first-only cell and is covered by the focused tests.

**Rejected alternatives.** Merely increasing the chance of partial overlap leaves deterministic branch omissions. Requiring different shapes is insufficient because one can still be a strict subset. Resampling whole lessons until aggregate coverage appears would make individual examples weaker, hide rejection rates, and leave exact override behavior probabilistic.

## D2 / R1 — Enumerate complete fixed-polyomino support, then place with a total fallback

**Choice.** `_polyominoes(size)` enumerates all translation-normalized fixed 4-connected shapes for sizes 3–6. The normal path samples this support; after bounded random attempts, a deterministic scan finds a valid shape pair and separated placement.

**Why.** This preserves broad geometry while making every advertised motif-size combination realizable. It also makes Python hash randomization irrelevant; the task test checks identical output under two `PYTHONHASHSEED` values.

**Rejected alternatives.** A small hand-written motif catalog would create a shape shortcut. Unbounded rejection sampling can hang or become seed-sensitive. Returning a fallback canned grid would violate exact size controls and collapse diversity.

**Probe.** [`repo/generators/57df2ac388cd/workspace/reference_probe.py`](repo/generators/57df2ac388cd/workspace/reference_probe.py) exposes normalized branches and the saved subset counterexample for future reviewers.

## D3 / R1 — Make every advertised axis exact and observable

**Choice.** Lawful axes are:

- `grid_h`: 9–16
- `grid_w`: 9–18
- `motif_a_cells`: 3–6
- `motif_b_cells`: 3–6
- `texture`: `default|warm|cool|varied`

Unknown overrides fail rather than being silently ignored. Negative fixtures reject ordinary axis combinations.

**Why.** The baseline exposed controls that did not alter returned grids. Silent controls poison curriculum balancing and make metadata untrustworthy. The final override report exercised 377 cases and 33,930 draws with zero findings: [`checks/after/checks/57df2ac388cd_after_override_results.json`](checks/after/checks/57df2ac388cd_after_override_results.json).

**Rejected alternatives.** Removing all axes would avoid the linter but make controlled data balancing impossible. Keeping aliases such as an ambiguous single `motif_cells` axis would obscure asymmetric size support.

## D4 / R1 — Fixed recoverable texture palettes; keep degenerates diagnostic-only

**Choice.** Helpful textures use disjoint fixed color pairs: default `(2,3)`, warm `(4,7)`, cool `(1,5)`, varied `(6,9)`. Degenerate inputs `no_motifs`, `single_motif`, and `all_same_color` remain callable validator fixtures but are not listed in `AXES`.

**Why.** A texture override should be inferable from the returned grid. Distinct palettes make the control exact and avoid output color 8 as an input-role color.

**Rejected alternatives.** Random palettes under a named texture make the control only statistical. Advertising malformed/negative fixtures as ordinary training values caused the baseline defect-lint failure. Arbitrary color permutations were not added because the task has scan-order roles and this review did not prove that every proposed role permutation is a lawful teaching counterfactual.

## D5 / R1 — Preserve canonical-scale support in every band

**Choice.** A 45% draw prior selects the canonical 9×9 profile unless an exact size override is supplied; otherwise difficulty-aware ranges expand geometry.

**Why.** The canonical examples are all 9×9, and the profile-floor gate requires support in each band. The final 20-draw-per-band result found exact hits easy 9, medium 11, hard 6, with no crashes: [`checks/after/checks/57df2ac388cd_after_profile_floor.json`](checks/after/checks/57df2ac388cd_after_profile_floor.json).

**Rejected alternatives.** Making every example 9×9 would overfit scale. Relying on wide uniform ranges gave no explicit canonical-support guarantee. The 45% value is a pragmatic prior, not an inferred property of the rule.

## D6 / R1 — Three demonstrations, named rivals, and required query-rotation census

**Choice.** `EXAMPLES_NEEDED = 3`. Every individual lawful grid carries all three branch witnesses, and each lesson is checked against `paint_overlap_first`, `erase_first_only`, and `erase_second_only`. Production order remains the materializer’s order; the final census additionally requires every one of the four labelled pairs to serve as the query once while preserving the remaining order.

**Why.** Three examples provide geometric variety without needing branch coverage to emerge by luck. Named rivals make “teachable” executable rather than descriptive. The final census materialized 100 lessons per band: 0/300 production ambiguities and 0/1,200 rotated-query ambiguities over 1,200 unique inputs, with no materialization/scoring errors: [`checks/lesson-census.json`](checks/lesson-census.json).

**Rejected alternatives.** One demonstration is too vulnerable to incidental geometry; adding more than three demos increases token cost without evidence it is needed for these declared rivals. The census does not claim universal induction or enumerate undeclared rules.

## D7 / R1 — Keep the Racket authority unchanged

**Choice.** Pin `RULE_HASH = "a668b763669f"`; do not edit the canonical Racket rule.

**Why.** Canonical outputs and the intended normalize-and-overlay rule were internally consistent. The defects were distribution, metadata, and teaching support. `rule_smoke`, `racket_lint`, and `authority_sync` are green in the final 12/12 battery report.

**Rejected alternative.** Broadening or rewriting the authority would turn a generator repair into a semantic task change without evidence.

## D8 — Known limits and audit-only decisions

The selected domain intentionally has exactly two separated monochrome motifs, sizes 3–6, on 9–16 by 9–18 grids. It does not cover arbitrary object counts, touching source objects, larger shapes, arbitrary palette permutations, or every plausible hypothesis.

**A1** and **A2** are audit-only findings. Their selected sources were left byte-for-byte unchanged. A1 recommends repairing the hard-band width calculation or bounding icon width; A2 recommends adding repeated-value rows so multiplicity is taught. Details and exact source hashes are in [`AUDIT.md`](AUDIT.md).
