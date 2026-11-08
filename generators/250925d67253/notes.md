# Working notes: 250925d67253

## Current native two-hop build (review-235c7c2a314684f0)

Native `route_policy=one_hop|two_hop` now preserves the exact canonical default
and adds input-dependent two-hop centroid addressing p[p[s]]. `adapter.py`,
`promotion.json`, `native.py`, `rules/two_hop.rkt` and reusable `audit.py` live in
`workspace/parametric/`. Historical transpose proposal remains separate.
Production source and canonical bytes are unchanged. Applying the canonical
program twice is NOT the alternate rule; the second address is read from the
original grid. The protected skip-second-address counterfactual is retained at
`checks/250925d67253/causal/witness.json` after qualification.

71 task tests passed. The bounded 20-seed audit exercised all count combinations,
800 requests / 200 unique grids, 2,000 masked public turns and 98 protected Racket
evaluations. Six competitors per selected setting were tested; no finite teaching
hole was found. The exact 19x19 law cannot lawfully reach 30x30. Inherited finite
motif support remains a limitation, not repaired or concealed. Both native owner
acceptance and any training admission remain pending. See workspace README for
replay commands and evidence pointers.


## Current review: review-2f4f897fe5f87c8d (2026-10-20)

The selected production generator remains version `3.0.0`, SHA-256
`bfc03f21b61f9e1f031a246e7c391a6d28cac4d3871c018f075efed8cb151c34`.
No production input-distribution or canonical Racket change was justified: the
fresh pinned before battery and final after battery are both 12/12 green, and
`RULE_HASH = 9f1390aa0494` remains bound to the same authority. The final
portable selected-task run is 62/62 green.

This review adds a separate **proposed** prototype under
`workspace/parametric/`. Its one episode-wide parameter is
`destination_frame = identity | transpose`. `identity` is the byte-identical
canonical/default rule; `transpose` preserves marker-centroid computation and
whole-panel copying but interprets each selected logical destination `(row,
column)` as `(column, row)`. The parameter is chosen once from the episode seed.
Exact Racket sources are materialized for both settings, and public challenge
content and filenames omit the hidden setting and query answers.

Retained prototype evidence is
`checks/parametric/destination-frame-final/report.json`: 8/8 canonical pairs,
10/10 Racket-labelled Python-parity checks, 2/2 complete lessons identifiable,
10/10 held-out-query rotations identifiable, and an 82-cell output-difference
witness. Program SHA-256 values are
`ea65e3b312617fb2193b451e7778bb6f237323224e5fd99599607dddf6b0b362`
for `identity` and
`d2d5fe704c4e691d84c14dad7cf3d28a6b46174f1299512240b59dad33599618`
for `transpose`. This is authoring evidence, not production integration or
training approval.

The fresh 100-lessons-per-band census retained 300 lessons, 1,500 unique
Racket-labelled pairs, and all 1,500 single-query rotations. No declared-rival
ambiguity, materialization error, hook warning, or scoring error was found.
The compact report is `checks/lesson-census-current.summary.json`; the complete
report is compressed with restoration hashes in
`checks/lesson-census-current-compression.json`.

Current limits: the prototype tests only two coordinate-frame settings and the
finite generated seeds; it does not prove unique induction against undeclared
programs. The production motif bank remains finite, and the canonical examples
still admit the documented centroid-proxy rivals even though generated lessons
refute them.

## Intended rule

The input is always 19×19. Rows and columns `0, 6, 12, 18` are zero separators around a row-major 3×3 array of 5×5 panels. One nonzero color is the common panel background and one is the common marker color. In each source panel, average the local row and column coordinates of **all** marker cells. Bucket each average with thresholds `<1.5`, `<=2.5`, `>2.5`; the resulting pair names the destination panel. The nine destinations must be a bijection. Copy each complete 5×5 source panel to its destination and preserve the separator lattice.

Canonical rule pin: `RULE_HASH = 9f1390aa0494`. The selected Racket behavior was not changed in review `review-0343e81b353c041a`; two archived base-solution fields were text-synchronized to their already-canonical `program_solution` so the authority-sync gate measures one representation.

## Reversed decisions in version 3.0.0

- **Prior choice:** every example used `(source + shift) mod 9`. **New choice:** draw either a non-affine 9-cycle derangement or a mixed-fixed permutation with a Sattolo cycle on the remaining slots. **Reason:** the old support let a solver inspect one panel, infer one shift, and ignore eight marker sets. The retained before battery and prior audits reproduced this shortcut.
- **Prior choice:** numerous declared axes were fixed, aliases, or degenerate textures. **New choice:** three exact observable axes only: `permutation_kind`, `marker_density`, and `palette_band`. Unknown, malformed, and incompatible inputs are rejected rather than silently ignored.
- **Prior choice:** random marker placement did not preserve canonical morphology or distinguish centroid proxies. **New choice:** sparse and dense asymmetric motif banks. Every marker component touches a panel boundary and therefore the separator lattice; row-0 occupancy keeps the authority's background vote unambiguous. Target-specific motifs force arithmetic-centroid outputs to differ from bounding-box-center, nearest-anchor, and coordinate-median rivals.
- **Prior choice:** validation checked little of the actual law. **New choice:** `self_check` validates dimensions, separators, palette, background inference, marker counts, target bijection, and the exclusion of global cyclic shifts. `strict_canonical_like` accepts all retained canonical inputs and the declared sampler manifold.
- **Prior choice:** no executable lesson contract. **New choice:** four semantic witnesses, four rivals, three canonical-fitting shortcut declarations, and `lesson_identifiable`. `EXAMPLES_NEEDED = 4`; production order is fixed by the materializer, but the contract also passes every held-out query rotation in the 300-lesson census.

## Distribution decisions

`derangement` draws a non-affine 9-cycle. `mixed_fixed` draws one to four fixed points and a Sattolo cycle over all remaining slots. Uniform cyclic permutations are rejected because they recreate the original shortcut. Low palettes draw two distinct colors from `1..4`; high palettes draw two from `6..9`. Sparse and dense motif supports overlap the canonical marker/component profile while staying exactly observable from an emitted grid.

The sampler deliberately does **not** include empty panels, all-marker panels, zero inside panel interiors, tied background votes, non-bijective destinations, or arbitrary grid sizes. Those cases are outside the canonical law or make the authority ill-defined. It also does not use color permutations across the fixed zero-separator role.

## Evidence and probes

- Current before battery: `checks/before/checks/250925d67253_before_battery_summary.json` (12/12 green).
- Current final battery: `checks/after/checks/250925d67253_after_battery_summary.json` (12/12 green), generator SHA-256 `bfc03f21b61f9e1f031a246e7c391a6d28cac4d3871c018f075efed8cb151c34`.
- Current portable selected tests: `checks/task-tests-final/result.json` (62 passed).
- Current large census: compact report `checks/lesson-census-current.summary.json`; full source-bound report `checks/lesson-census-current.json.gz` with restoration metadata in `checks/lesson-census-current-compression.json`. It materialized 100 lessons per band, 1,500 labelled pairs, and 1,500 held-out-query rotations with zero declared-rival ambiguity or scoring errors.
- Canonical shortcut probe: `workspace/probe_shortcuts.py`; exact retained witness `counterexamples/current-shortcut.json` and `checks/generator-shortcut-final/`.
- Fresh exposed solve: `solve/summary.json` (revision 1 matched all four visible examples; no reference consulted during the solve episode).

## Known limits and open findings

The canonical demonstrations themselves do not distinguish arithmetic centroid from bounding-box center, nearest 0/2/4 anchor, or coordinate median: each fits all eight canonical/augmented pairs returned by the portable helper. The generated distribution deliberately refutes them, but this is a finite rival set, not a proof of unique induction.

The motif support is a finite bank (two variants for each target in each density band). A learner could memorize those templates instead of computing centroids. The palette, source position, permutation, and motif variant still vary, and all declared/generic rivals were refuted in the retained census, but procedural motif expansion would be the next distribution-hardening step.
## Archived production-repair rationale from the accepted version

The sections below preserve why version 3.0.0 was previously repaired. They are historical context, not evidence of a new defect in this review.

Source SHA-256: `bfc03f21b61f9e1f031a246e7c391a6d28cac4d3871c018f075efed8cb151c34`.

# Decisions — 250925d67253

## D1: Replace the uniform cyclic family

**Prior choice.** Version 2.0.1 drew one shift in `1..8` and assigned every source `s` to `(s + shift) mod 9`. The likely original rationale was simplicity: it guaranteed a bijection and made centroid placement easy.

**Failure mode.** The first panel's marker centroid revealed the shift. A rival could ignore the other eight marker sets and still solve every generated input. The pinned before battery and retained audit lead both exposed this, and the old generator's source made it exact rather than hypothetical.

**New choice.** `permutation_kind=derangement` draws a non-affine 9-cycle. `permutation_kind=mixed_fixed` draws one to four fixed points, then a Sattolo cycle on the remaining slots. Every mapping is a bijection and no mapping is a uniform cyclic shift.

**Rejected alternatives.** Merely randomizing the shift between demonstrations still leaves the one-marker shortcut valid within each puzzle. Arbitrary `random.shuffle` alone was rejected because it could occasionally regenerate the original cyclic family and because an exact control would be difficult to observe. A full derangement-only family was rejected because canonical examples include fixed behavior and a mixed family broadens structure without weakening the rule.

**Probe.** Joint-axis tests inspect the inferred source→target mapping for every override combination; default-sampling tests reject uniform cyclic mappings and check replay/diversity. See `repo/generators/250925d67253/tests/test_generator_repair.py`.

## D2: Expose only semantic, observable controls

**Prior choice.** The generator advertised grid height/width, shift, palette kind, corner anchors, asymmetry, palette size, position bias, distinct-color count, texture aliases, and degenerate textures. Several were fixed values, aliases, or modes that did not belong to the canonical task.

**New choice.** The public axes are:

- `permutation_kind`: `derangement|mixed_fixed`;
- `marker_density`: `sparse|dense`;
- `palette_band`: `low|high`.

Every joint combination is constructive and recoverable from the generated grid through `observe_overrides`. Unknown keys, malformed values, invalid difficulty, boolean-as-integer seeds, and invalid sample indices raise rather than silently coerce.

**Rejected alternatives.** Keeping compatibility aliases was rejected because the override gate should test actual semantics, not historical names. Degenerate inputs (`no_markers`, `full_grid`, or one active panel) were rejected because the Racket authority divides by marker count or expects a nine-way bijection. Arbitrary dimensions were rejected because separator positions are part of the rule.

## D3: Use canonical-like, separator-connected marker motifs

**Goal.** Preserve the intended centroid law while matching the canonical topology closely enough that component-count and object-profile checks are meaningful.

**New choice.** Each target has two sparse and two dense motifs. Every component touches a local panel boundary, so every non-background structure meets the global zero lattice. Marker counts stay in the validated `[2,16]` interval. At most two top-row markers occur in a motif, preserving an unambiguous row-1 background vote across the three top panels.

**Rejected alternatives.** Fully independent random marker cells were rejected after strict distribution analysis found topology/component mismatches and ambiguous background voting. Requiring one connected marker object was rejected because canonical inputs can have multiple components. Singleton-heavy templates were removed because the canonical support and generated support did not overlap. Procedural rejection sampling was considered but deferred: it can offer broader support, yet would need careful performance bounds and a proof that every target/proxy condition remains satisfiable.

**Known limit.** The current bank has 36 templates and can be memorized. This is documented rather than hidden. The next improvement should procedurally perturb or synthesize motifs under the same centroid, topology, background-vote, and rival-refutation constraints.

## D4: Make canonical-fitting proxy rules executable

The portable canonical helper returns eight usable canonical/augmented pairs. Three plausible alternatives fit all eight:

1. bucket the center of the marker bounding box;
2. assign the arithmetic centroid to the nearest anchors `0,2,4` instead of thresholding at `1.5/2.5`;
3. bucket the coordinate-wise marker median.

The strongest simple rival is bounding-box center. It is easy to state, uses all marker cells, and exactly matches every retained canonical pair. The generator now declares all three in `CANONICAL_SHORTCUTS` and constructs every sample so they disagree with the intended output. The exact seed-0 witness is retained in `counterexamples/current-shortcut.json` and bound to the public Racket authority in `checks/generator-shortcut-final/verification.json`.

**Rejected alternative.** Treating canonical fit as proof that the canonical rule should be changed was rejected. The selected Racket program and rule hash explicitly use arithmetic means and threshold boundaries; the issue is demonstration ambiguity, not authority uncertainty.

## D5: Four demonstrations and query policy

`EXAMPLES_NEEDED = 4` is retained. Each generated input independently contains a complete nine-panel permutation, but four examples reduce overfitting to incidental palette or motif choices and match the existing solve materializer. Production lesson order is the order returned by the materializer.

Unlike an intentionally ordered-only curriculum, this generator claims rotation robustness against its declared rivals. The required-rotation census held out every one of five labelled pairs in every materialized lesson: 300 production lessons, 1,500 pairs, and 1,500 rotations, all with zero ambiguity or scoring errors. This is finite-rival evidence only; it does not enumerate all programs or every random seed.

**Rejected alternatives.** Reducing to one demo was rejected because the task's semantics are subtle and the canonical examples admit proxy rules. A schedule-specific curriculum was unnecessary because every emitted input itself refutes all four declared competitors.

## D6: Strengthen validation rather than normalize bad inputs

`self_check` now validates exact shape, cell types/range, separator rows/columns, nonzero panel interiors, exactly two nonzero colors, a unique inferred background, one marker color, marker counts, a nine-way centroid bijection, and non-cyclic mapping. `strict_canonical_like` intentionally delegates to the same law and accepts all retained canonical inputs.

**Rejected alternatives.** Repairing malformed grids inside the checker was rejected because it hides generator defects. Accepting global cyclic maps as lawful but “rare” was rejected because the training support must not reintroduce the original shortcut. Collapsing rival target collisions nondeterministically was rejected; rival output uses the first source deterministically so semantic diagnostics are replayable.

## D7: Synchronize archived Racket text without changing the rule

The selected canonical `program_solution` was already correct. Two base-solution JSON files held behaviorally equivalent but text-divergent `raw_code` and `target_code`, which caused `authority_sync` to fail.

The review copied the existing `program_solution` text into those two fields. No canonical puzzle row, rule hash, or Racket semantics changed. The final battery's `rule_smoke`, `racket_lint`, and `authority_sync` stages are all green.

**Rejected alternative.** Weakening the synchronization check or marking the mismatch advisory was rejected because a single textual authority is safer for future agents and easier to hash.

## D8: Build a reusable shortcut probe

`workspace/probe_shortcuts.py` loads the selected source portably, scores every declared canonical shortcut on `reviewer_support.canonical_pairs`, and writes one deterministic emitted counterexample with source hashes. It deliberately leaves authority execution to the public `arcpuzzles apply` command so a Python mirror cannot masquerade as the Racket label.

A focused test was written first and failed because the tool was absent (`checks/tdd-probe-red.log`); it then passed after implementation (`checks/tdd-probe-green.log`). Usage is in `workspace/README.md`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-7e59c84bf90dd5ed:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `1c8793c4cbdaa67a81d4db0d121d587b2f37a21259445abf7674fd6d43b77d7c`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicitly resolve old1c8793c4 global-cyclic/one-marker teaching shortcut using current selected bfc03f21 source, unchanged by this prototype-only return. Source _draw_permutation rejects uniform cyclic maps; self_check rejects them; one_marker_global_shift is executable SEMANTIC_RIVALS/LESSON_COMPETITORS and tests/test_generator_repair.py checks noncyclic mapping and rival disagreement. Reviewer remeasured62 portable cases,12/12 before/after batteries and300 lessons/1500 rotations with0 declared-rival ambiguity. Current independent centroid bijection addresses both old reports; no universal/undeclared-program proof or owner test rerun.

### Assessment or prior finding

## 250925d67253

**Reproduced semantic shortcut — one marker determines a global cyclic shift.**

The generator assigns every source cell destination `(source_index + shift) mod 9`. For the default-domain case `seed=0`, `sample_index=0`, `difficulty="medium"`, the nine centroid destinations are

```text
[8, 0, 1, 2, 3, 4, 5, 6, 7]
```

so every per-source shift is 8. A rival can read only source cell 0's centroid, ignore the other eight marker configurations, and apply that single cyclic shift to all nine cells. Its output exactly matches the canonical Racket output for the generated grid.

Canonical train example 0 refutes the rival: its destination mapping is

```text
[0, 3, 8, 2, 6, 5, 4, 7, 1]
```

with per-source shifts `[0,2,6,8,2,0,7,0,2]`; the same one-marker shortcut gives a different output. Both inputs pass the selected generator's `self_check`. Exact inputs, Racket outputs, rival outputs, hashes, and the supported apply command are retained in:

- `checks/audit/250925d67253/counterexample/input.json`
- `checks/audit/250925d67253/counterexample/racket.json`
- `checks/audit/250925d67253/counterexample/rival.json`

Generator SHA-256: `1c8793c4cbdaa67a81d4db0d121d587b2f37a21259445abf7674fd6d43b77d7c`. Executed rule hash: `9f1390aa0494`.

**Suggested repair:** sample a genuine arbitrary/non-affine permutation of the nine targets, then synthesize each source cell's marker centroid independently from its assigned destination. Include a rival that reads only one marker and assert it fails generated lessons.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-7e59c84bf90dd5ed-v0001/audit_assets.json), manifest SHA-256 `f99ad721ca4a05a117196e4065312a292555201f10772e6c91dab81abe247d2e`.
<!-- arcpuzzles-current-audit-assessment:end -->

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/250925d67253/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
