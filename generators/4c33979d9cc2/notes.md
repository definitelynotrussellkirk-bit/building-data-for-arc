# Working notes: 4c33979d9cc2

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `3aef539d4a88965100b69ae4be94ea8e7e872fb9d97134f8645037a977b54696`.

# Decisions: 4c33979d9cc2

## D1 — Treat the canonical Racket rule as authoritative

**Choice.** Define the task as repainting only the unique largest orange component red, while preserving every smaller orange component and every background cell.

**Original rationale.** Unknown. The imported baseline prose instead described keeping the largest orange and erasing the rest, which contradicted the canonical pairs and selected Racket program.

**Alternatives considered.** Preserve the baseline prose; rewrite the Racket rule to match it; or treat the canonical row as authority. The first two would change the task and fail all canonical outputs, so they were rejected.

**Probe.** The Python mirror matches all three canonical pairs exactly; the Racket smoke stage passes.

**Failure mode / limitation.** The selected Racket rule assumes at least one orange component. The generator and `self_check` enforce 2-5 components, so that undefined case is outside the generated manifold.

## D2 — Use 2-5 components instead of exactly three

**Choice.** Vary the observable component count across 2-5.

**Original rationale.** The baseline fixed three components, apparently as a simple imported template; no task-specific justification was recorded.

**Alternatives considered.** Keep exactly three; use 1-8; or use 2-5. Exactly three creates a count shortcut and poor coverage. One component makes the selection rule trivial. More than five materially raises placement failures in the smallest grids without adding a new semantic branch.

**Probe.** The stress census covers every count in the declared range, and full boundary overrides pass in all bands.

**Failure mode / limitation.** The canonical rule works for more than five objects, but this curriculum does not cover that scale.

## D3 — Require one unique largest component but allow smaller ties

**Choice.** Component sizes vary from 1-8. Exactly one component must have maximal cell count; any subset of smaller components may tie.

**Original rationale.** The baseline hard-coded distinct sizes `5, 3, 2`, which made "fixed size 5" and "all sizes distinct" accidental rules.

**Alternatives considered.** Keep all sizes distinct; allow tied maxima; or allow only one non-winner. Tied maxima make the selected rule ambiguous because the Racket sort has no task-level tie semantics. Smaller ties are lawful and specifically rebut the distinct-size shortcut.

**Probe.** Mutation tests reject tied maxima; canonical test input with equal smaller sizes is accepted; the `nonlargest_tie_diagonal` profile guarantees a smaller tie.

**Failure mode / limitation.** Maximum generated component size is 8, so size generalization beyond 8 depends on learning the comparison rule rather than direct exposure.

## D4 — Use a finite connected-shape library with D4 transforms

**Choice.** Draw compact and sparse polyominoes for each size and apply rotations/reflections.

**Original rationale.** The baseline used a generic growth helper. It gave stochastic morphology but no way to guarantee a bounding-box counterexample.

**Alternatives considered.** Pure random growth; exhaustive free-polyomino enumeration; or a small curated library. Pure growth made semantic witnesses probabilistic. Exhaustive enumeration was unnecessary for this easy rule and would increase code and audit surface. The curated library gives deterministic witness construction while retaining orientation variety.

**Probe.** The stress census observed 378 component-size vectors and 53 dimension profiles, and the semantic witness for a larger non-winner bounding box fires on schedule.

**Failure mode / limitation.** The shape library is finite and favors small 1-3-row motifs.

## D5 — Forbid orthogonal merging but permit diagonal-only contact

**Choice.** Placement requires a one-cell orthogonal separation between components, but diagonal adjacency is lawful and deliberately scheduled.

**Original rationale.** The baseline rejected overlapping bounding boxes, which also removed many lawful close layouts and made segmentation artificially easy.

**Alternatives considered.** Bounding-box isolation; full 8-neighbor isolation; or only 4-neighbor separation. The selected rule identifies 4-connected objects, so 4-neighbor separation is the task-faithful boundary.

**Probe.** The `nonlargest_tie_diagonal` profile produces two orange components that touch diagonally yet remain distinct under 4-connectivity; the 8-connected rival then disagrees with the canonical rule.

**Failure mode / limitation.** Components never share an edge, because that would make them one 4-connected object.

## D6 — Use a deterministic five-profile lesson schedule

**Choice.** Set `EXAMPLES_NEEDED = 5` and cycle through `largest_first_edge`, `largest_last_interior`, `bbox_area_decoy`, `nonlargest_tie_diagonal`, and `two_components`.

**Original rationale.** The baseline had no lesson schedule or semantic coverage target.

**Alternatives considered.** Fully random examples; a three-example cycle; or the five-profile cycle. Random generation could produce many valid examples while never falsifying a shortcut in a particular lesson. Three examples could not simultaneously guarantee order, extent, tie, connectivity, edge, and two-object contrasts without overloading scenes. Five keeps each example legible.

**Probe.** Every consecutive five-example lesson is checked against all named competitors; every scheduled witness fires in each difficulty band.

**Failure mode / limitation.** The cycle is visible in `sample_index`; materializers that always request the same index would collapse the curriculum.

## D7 — Anchor one empirical canonical size per band

**Choice.** The `two_components` slot uses `6x7`, `7x8`, and `9x9` in easy, medium, and hard respectively, unless dimensions are explicitly overridden.

**Original rationale.** The first repair used disjoint hard-band dimensions, which passed pooled distribution checks but failed the per-band canonical-profile floor.

**Alternatives considered.** Widen every band's random range to include all canonical dimensions; opt out of the profile gate; or dedicate one scheduled anchor. A scheduled anchor gives deterministic support without collapsing the rest of each band's scale variation.

**Probe.** The first after run failed hard-band support. The added regression test failed before implementation and passes now. The pinned `profile_floor` stage and the 3,720-draw census pass.

**Failure mode / limitation.** The profile gate defines a profile by dimensions and palette size, not complete object morphology; the semantic gate and task tests cover the stronger rule properties.

## D8 — Expose only exact, recoverable axes

**Choice.** Public axes are `grid_h`, `grid_w`, and `n_components`.

**Original rationale.** The baseline declared palette, density, texture, position, and color-count axes that were inert, aliased, or inconsistent with the actual two-color task.

**Alternatives considered.** Preserve compatibility aliases; add profile as a public axis; or keep only observable exact axes. Compatibility aliases would continue producing misleading provenance. The internal semantic profile is intentionally a curriculum schedule, not an independent public degree of freedom.

**Probe.** `observe_overrides` recovers all three values from the returned grid; all lower/upper/cross-corner override combinations pass; unknown keys fail loudly.

**Failure mode / limitation.** Callers cannot directly request a semantic profile. They select it through `sample_index`, keeping lesson ordering centralized.

## D9 — Make validation and semantic contracts executable

**Choice.** Add strict structural validation, a Python rule mirror, witnesses, rival programs, canonical shortcuts, and `lesson_identifiable`.

**Original rationale.** No prior semantic contract existed, and the baseline `self_check` could approve ambiguous scenes.

**Alternatives considered.** Rely only on the Racket smoke test; add random property tests; or expose task-local contracts consumed by the shared semantic gate. The selected approach makes both lawful-input boundaries and specific wrong hypotheses reproducible.

**Probe.** Ten task-local tests pass; the shared `selfcheck` and `semantic_gate` stages pass; `checks/shortcut_probes.json` shows the two canonical-fitting shortcuts are killed by the schedule.

**Failure mode / limitation.** Named rivals are not exhaustive. Future audits should add newly discovered compact shortcuts rather than assuming the current list proves uniqueness over all possible programs.

## D10 — Synchronize selected Racket text exactly

**Choice.** Remove the task-local comment so `target_code` is byte-for-byte equal to canonical `program_solution` after JSON decoding.

**Original rationale.** The baseline comment was behavior-neutral, but the authority policy intentionally treats exact selected-source drift as a failure.

**Alternatives considered.** Leave comment-only drift; add the comment to shared canonical data; or synchronize the task-local selected source. Editing the task-local file was the smallest allowed change and preserved behavior and `RULE_HASH`.

**Probe.** `racket_lint`, execution parity, and `authority_sync --require-selected-exact-sync` pass.

**Failure mode / limitation.** `raw_code` remains archival; selected authority is `program_solution`/`target_code`.
