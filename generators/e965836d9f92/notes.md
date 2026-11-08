# Working notes: e965836d9f92

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `b93666cd030874e8e91049d9de47be6d539c492d3e8bccad50b1e9c2847e6ae3`.

# Decisions for `e965836d9f92`

## D1 — Preserve the selected Racket authority

**Choice.** Keep canonical `RULE_HASH=29642118732e` and repair only the generator curriculum.

**Rationale.** The canonical, selected, and executed authority are synchronized. Its first-panel footprint and clipping behavior are visible in canonical outputs; changing it would be a semantic migration, not a generator repair.

**Rejected alternative.** Resize every gallery panel to the maximum transformed dimensions. That is arguably cleaner, but it changes canonical answers and requires an atomic rule/canonical migration.

**Evidence.** Final `authority_sync` is green in `checks/after-final-v331/`; canonical SHA-256 remains `f5aa554e2aa0959cddca2a4a693e3524f8ad2836fbdff7f85a481058bcded6ee`.

## D2 — Use a nine-slot rotation-complete schedule

**Choice.** Use three canonical anchors and three noncanonical code profiles in this cycle:

`C, N1, N2, C, N3, N1, C, N2, N3`, where `C=(1,2,3)`, `N1=(1,4,5,6)`, `N2=(2,4,5,6)`, and `N3=(3,4,5,6)`.

**Rationale.** Every transform code occurs at least twice in every cyclic four-slot window. With three demonstrations and one query, any held-out position therefore leaves at least one direct witness for every code.

**Rejected alternatives.** The baseline three-profile pattern failed 8/72 smoke rotations. A balanced four-slot repair fixed rotations but produced only 139/600 strict canonical hits (23.2%), below the declared 25% floor. Lowering the floor would conceal the distribution regression rather than fix it.

**Failure modes and limits.** This argument is specific to four-pair lessons and the current six-code profile family. A future change to `EXAMPLES_NEEDED`, schedule period, or code profiles must rerun all cyclic starts.

## D3 — Use square transform-separating noncanonical defaults

**Choice.** Noncanonical defaults use connected square-bounded prototypes whose six dihedral transforms are distinct.

**Rationale.** Under the selected authority, rectangular quarter turns can be clipped to the first panel footprint, making wrong transform mappings answer-equivalent. Square footprints remove that ambiguity without changing the authority.

**Rejected alternative.** Change the Racket gallery sizing rule. Rejected under D1 because it changes canonical semantics.

**Failure modes and limits.** Exact overrides can still request `proto_size=4`, for which no connected four-cell polyomino has six distinct transforms in a square bounding box. This remains an allowed boundary case and is tested by the override contract; the stronger square guarantee applies to default teaching profiles.

## D4 — Make semantic rivals executable and named

**Choice.** Declare one wrong mapping for each transform code, plus rivals for ignoring codes, using header rank, reusing the first output color, preserving the prototype color, and reading physical header rows/columns as values. Bind each semantic witness to at least one named rival.

**Rationale.** A witness is useful for training-data quality only when it certifies disagreement with a plausible wrong rule. The original morphology-only declarations could fire while proving no answer difference.

**Rejected alternative.** Count feature presence alone. Rejected because the strict gate correctly classified those witnesses as weak.

**Failure modes and limits.** The rival registry is finite. Passing it does not rule out undeclared hypotheses.

## D5 — Force every noncanonical pair to refute physical-position decoding

**Choice.** Preserve the initially sampled header locations unless they are contiguous or their coordinates decode to exactly the same values as the header contents; otherwise choose a deterministic valid fallback. Apply the same policy to transform columns and output-color rows.

**Rationale.** The 300-lesson version-3.3.0 census found two exact leave-one-out failures. In both, the only remaining noncanonical demonstration had column positions whose modulo-6 values equaled its transform codes, so `header_column_is_transform_code` fit all demonstrations and disagreed on the held-out query.

**Rejected alternatives.** Removing the physical-position rivals would hide a reproducible shortcut. Resampling whole instances would make lesson assembly nondeterministic and could still admit the collision. Treating the large census as a false positive was rejected because arbitrary query rotation is explicitly supported here.

**Probe.** `checks/lesson-census-final-v33-ambiguities.json` retains the two source-bound failures; the corresponding regression is red before and green after the helper.

## D6 — Keep two levels of identifiability checking

**Choice.** Retain the shared Racket-backed census and add a fast task-local exhaustive schedule probe that dynamically reads `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, `SEMANTIC_WITNESSES`, and `WITNESS_RIVALS`.

**Rationale.** The shared census validates real materialization and Racket labels over 100 lessons per band. The local probe cheaply enumerates all schedule starts, many seeds, every query rotation, direct code coverage, square footprints, and all declared rivals.

**Rejected alternative.** Rely only on the 12-lesson semantic smoke test. Version 3.3.0 passed that test but failed 2/1,200 rotations in the larger census.

**Limits.** The local probe uses the Python rule mirror; it cannot replace Racket-backed checks. The final local sample is finite: 1,800 windows, 7,200 rotations, and 7,149 unique inputs.
