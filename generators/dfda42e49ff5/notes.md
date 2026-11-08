# Working notes: dfda42e49ff5

Final reviewed generator: version `2.1.0`, SHA-256 `fa671057ba0034699739a72d6f840e7ec00b0f3a85a176bad566db9f3c9ab291`, canonical `RULE_HASH` `2241d1285117`.

## Intended rule

For every same-color four-connected object, independently fill each occupied row from that row's leftmost object cell through its rightmost object cell. Disconnected objects remain separate even when they share a color. The Racket authority and canonical examples were not changed.

## Reversed baseline decisions

Version 1.3.0 used a five-entry/four-effective-shape bank, forced every motif to have a distinct color, advertised nine controls that were not all truthful exact axes, and included blank/identity degenerates. That combination made template memorization and “one object per color” viable while failing lint, canonical self-check, profile-floor, and override contracts.

Version 2.1.0 dynamically constructs connected motifs and advertises only one exact axis, `scene_profile`. Unknown override names raise. The public schedule cycles deterministically through:

- `canonical_single` — one 5-row object at width 7, 8, or 9;
- `same_color_pair` — two disconnected same-color objects on overlapping rows;
- `same_color_trio` — three disconnected objects of one color;
- `mixed_cluster` — a same-color pair plus a third object of another color.

The rich profiles teach the component distinction. Motifs also vary row-specific right boundaries so that “extend each row to the component-wide right edge” is decisively wrong.

## Executable semantic contract

Declared rivals: `per_color_row_span`, `largest_component_only`, `component_bbox_fill`, `component_global_right_span`, and `one_cell_per_gap`. Each has a causal witness. `lesson_identifiable` requires at least three demonstrations and rejects a lesson when any declared competitor survives them.

Independent probes live in `workspace/reference_probe.py`. Minimal retained counterexamples live under `counterexamples/` and are covered by focused tests.

## Final evidence

- Required-rotation battery: 12/12 green (`checks/final2-after/`).
- Task-local tests: 54/54 passing (`checks/final2-task-tests/result.json`).
- Lesson census: 300/300 materialized, 0 production ambiguities, 0/1,200 ambiguous query rotations, 1,006 unique inputs (`checks/final2-lesson-census.json`).
- Post-repair visible solve: 3/3 examples, final generator bytes, no reference consulted during the solve (`solve/summary.json`).

## Limits and open status

The live domain requires a one-cell zero moat, at most six components, and at least one horizontal row gap per object. The motif family retains a solid connector row and therefore has a construction fingerprint. Finite rival/census results do not prove uniqueness against undeclared hypotheses or all seeds. There are no open repair blockers; catalog approval remains unchanged.

Imported associated notes were empty, so no prior return was used as a lead.
## Current reviewer considerations

Source SHA-256: `fa671057ba0034699739a72d6f840e7ec00b0f3a85a176bad566db9f3c9ab291`.

# Decisions for `dfda42e49ff5`

Final generator SHA-256: `fa671057ba0034699739a72d6f840e7ec00b0f3a85a176bad566db9f3c9ab291`
Version: `2.1.0`
Rule hash: `2241d1285117`

## D1 — Preserve the canonical Racket authority

**Decision.** Keep the existing Racket rule and canonical examples unchanged. Repair only the Python generator, its task-local tests/tools, notes, and counterexamples.

**Reason.** Independent inspection and Racket application agreed on the intended transformation: fill horizontal spans per same-color four-connected component, row by row. Baseline failures were generator-contract and teaching-distribution defects, not authority defects.

**Evidence.** Final rule smoke and authority synchronization are green in `checks/final2-after/`; both retained counterexamples have `rule_hash_matches_catalog: true`.

**Rejected alternative.** Editing the Racket rule to match the baseline's per-color behavior. That would silently change a valid task and erase the component distinction rather than teach it.

## D2 — Replace fixed silhouettes with dynamic connected motifs

**Prior choice.** Version 1.3.0 chose from a five-entry `GAP_SHAPES` list containing one duplicate, so only four effective silhouettes were available.

**New choice.** Construct each motif from a solid connector row plus two or more gappy rows, with randomized inward extensions, connector side, widths, heights, and row-specific outer boundaries.

**Reason.** Template recognition was a much easier shortcut than inferring the rule. Dynamic construction produces many legal instances while preserving transparent structural guarantees.

**Probe.** Focused tests sample 128 instances per difficulty band and check diversity, lawful components, causal changes, and reference-oracle agreement. Final portable tests: 54/54 passing (`checks/final2-task-tests/result.json`).

**Rejected alternative.** Merely adding more hand-written templates. This would enlarge but retain a finite memorization bank and make structural guarantees harder to audit.

## D3 — Reduce the exact control surface to one truthful axis

**Prior choice.** The baseline advertised nine controls (`grid_h`, `grid_w`, palette and motif controls, density, position bias, texture), but several were aliases, ignored, inconsistent with the live domain, or represented identity/blank degenerates.

**New choice.** Advertise only `scene_profile`, with four exact values. Reject every unknown override key. `observe_overrides` reports the realized profile.

**Reason.** A smaller exact contract is better than an expansive false one. Grid dimensions and colors remain genuine stochastic variation rather than pretending to be exact controls.

**Alternatives rejected.** Retaining exact grid dimensions would require a much more complex feasibility solver for every profile and would add no semantic coverage. Retaining degenerate textures would produce blank/identity examples that do not teach the transformation.

## D4 — Use a deterministic four-profile teaching schedule

**Decision.** `sample_index % 4` cycles through `canonical_single`, `same_color_pair`, `same_color_trio`, and `mixed_cluster`. Difficulty affects rich-scene size, not semantic profile availability.

**Reason.** Every four consecutive production samples contain canonical-scale support and three stronger multi-object lessons. This prevents a random run from accidentally omitting the component distinction.

**Distribution rationale.**

- `canonical_single` keeps direct support for the 5-row, width-7/8/9 canonical envelope.
- `same_color_pair` is the minimal decisive witness against merging by color.
- `same_color_trio` makes “only process two” and “largest only” less plausible.
- `mixed_cluster` separates object identity from color identity while preserving same-color disconnection.

**Rejected alternative.** Pure random profile selection. It would make semantic coverage probabilistic and weaken short lessons and small sample audits.

## D5 — Keep disconnected objects of the same color

**Decision.** Three rich profiles deliberately place disconnected same-color objects on overlapping rows, separated by a one-cell moat.

**Reason.** All canonical pairs contain one foreground component, so `per_color_row_span` fits 3/3 canonical demonstrations. Distinct colors, as in the baseline, make that shortcut observationally identical to the intended component-wise rule.

**Counterexample.** `repo/generators/dfda42e49ff5/counterexamples/per_color_row_span_case.json`; authoritative output in `checks/counterexamples-final/per_color_racket.json`.

## D6 — Vary row-specific component boundaries

**Decision.** Every constructed motif has one gappy row that ends before the component-wide right edge and another row that reaches it; connector side and additional bounds vary.

**Reason.** Late shortcut review found `component_global_right_span`: start at each row's leftmost cell but always extend to the object's global right edge. It fits all three canonical demonstrations and survived an earlier repaired lesson rotation.

**Counterexample.** `repo/generators/dfda42e49ff5/counterexamples/component_global_right_span_case.json`; authoritative output in `checks/counterexamples-final/global_right_racket.json`.

**Rejected alternative.** Merely declare the rival and rely on resampling. The underlying distribution should causally refute the rival, not hope that a rare sample does.

## D7 — Make semantic claims executable

**Decision.** Declare five independent competitors and five witnesses, and require `lesson_identifiable` to reject a 3-demonstration lesson whenever a competitor survives.

**Competitors.** `per_color_row_span`, `largest_component_only`, `component_bbox_fill`, `component_global_right_span`, and `one_cell_per_gap`.

**Reason.** Correct individual labels do not guarantee that demonstrations identify the intended rule. Executable rivals convert prose intentions into replayable checks.

**Evidence.** The final semantic gate checks 12 materialized lessons and 48 query rotations; the larger census checks 300 lessons and 1,200 rotations. All declared rivals are refuted in every materialized lesson (`checks/final2-lesson-census.json`).

## D8 — Add an independent task-local oracle and retained fixtures

**Decision.** Add `workspace/reference_probe.py`, focused tests, and two minimal JSON counterexamples. The probe re-derives components and rival outputs independently of the generator's mirror.

**Reason.** Testing `rule_mirror` only against itself would not detect shared implementation mistakes. Racket-labelled fixtures bind the intended output to the actual authority.

**Evidence.** `repo/generators/dfda42e49ff5/tests/test_generator.py`, `repo/generators/dfda42e49ff5/workspace/reference_probe.py`, and `checks/counterexamples-final/`.

## Known limits

- Rival coverage is finite. Passing the declared family does not prove unique induction against every program.
- The motif family intentionally uses one solid connector row; a learner could exploit that construction detail even though the target transformation does not require it. Random connector side and row-bound variation reduce, but do not eliminate, generator-family fingerprints.
- The validator requires each object to have at least one horizontal gap, a one-cell zero moat between components, at most six components, and dimensions no larger than 30×30. This is the reviewed live domain, not the full mathematical domain of the Racket rule.
- The 300-lesson census samples 100 production lessons per band. Its 1,200 rotations hold out every pair in those bundles once, but it does not enumerate every possible seed/sample-index combination.
- Catalog approval remains unchanged; this review supplies evidence but does not admit training data.
