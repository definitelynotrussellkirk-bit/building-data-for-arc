# Working notes: 148cea0afb09

## Baseline measurement

- Assigned source SHA-256: `9a14b7979679820103bf028f18d388bae93502c6aca6b211fb19381bb59f7d5f`.
- Before battery: 6 green, 1 advisory, 5 failed (`lint`, `selfcheck`, `defect_lint`, `profile_floor`, `override`).
- Root causes reproduced in task-local tests: canonical solid-rectangle rejection; permissive/non-exact overrides; invalid fallback/texture assumptions; no executable semantic contract.
- Independent canonical comparison found that bbox-area ranking matched all 5 labeled pairs, making it a plausible shortcut requiring generated counterexamples.

## Repair

- Replaced rejection-heavy/random texture generation with deterministic fixed-polyomino schedules and backtracking placement.
- Advertised only exact, observable axes and rejected unknown keys; declared the only impossible rank/component tuple.
- Kept the Racket authority and `RULE_HASH=c113614858b9` unchanged.
- Added a bbox-area rival contract and 4-demo/1-query lesson-identifiability hook.
- Added `tests/test_generator.py` and reusable `workspace/review_probe.py`.

## Self-review revision

The first repaired schedule passed the mechanical gates but used a narrow fixed size profile, so rank could partially map to an absolute selected-object size. A failing regression was captured in `checks/tdd-red-absolute-size.log`; v2.1.0 now enumerates varied legal cell-count/bbox-area schedules and the final suite has 40 tests.

## Final evidence

- Final generator SHA-256: `535633b6aff64fd4249d9f481756f725c0cbfa76b9cd0376a248ac054ac07b12`.
- Final battery: 12/12 green.
- Portable task tests: 40/40 passed.
- Lesson census: 300 lessons, 1,500 pairs, 1,500 required query rotations, zero reported ambiguity/materialization/scoring/hook errors.
- Independent audit: 1,000 samples, zero validation/determinism/observer errors, bbox rival refuted in all 1,000; real Racket parity 37/37.
- Post-repair visible-only solve: revision 1 passed 4/4 visible examples; private labels remain unknown; earlier rule exposure correctly declared `yes`.

## Limitations

- The lesson result is finite and scoped to the declared bbox-area rival; it is not universal identifiability proof.
- Shape support is intentionally compact (3–8 cells) and difficulty varies canvas defaults rather than rule depth.
- Catalog approval, train safety, and training admission remain unverified/false pending maintainer action.
## Current reviewer considerations

Source SHA-256: `535633b6aff64fd4249d9f481756f725c0cbfa76b9cd0376a248ac054ac07b12`.

# Decisions — 148cea0afb09

## Canonical authority

**Decision:** keep the canonical Racket program unchanged and pin `RULE_HASH = "c113614858b9"`.

**Rationale:** the canonical rule already maps all five labeled pairs consistently: clear `(0,0)`, rank 4-connected objects by cell count, crop the selected object, and scale the crop by two. The observed failures were generator, validator, override, and teaching-data failures—not reference-label failures. The final authority hash is unchanged between the before and after batteries.

**Rejected alternative:** editing the Racket rule to encode generator-specific restrictions. That would convert a distribution defect into a rule change and would reject canonical-lawful inputs such as the solid rectangle.

## Component count and canonical profile

**Decision:** generate 2 or 3 separated components. Rank 3 forces 3 components; the only incompatible exact-axis tuple is `{n_components: 2, rank: 3}`.

**Evidence/rationale:** the five canonical inputs contain component counts `3, 3, 3, 3, 2`, with ranks spanning 1–3 and cell sizes spanning 3–8. The baseline summary claimed 3–4 components, but the fourth component was not supported by these examples and increased override complexity without adding a necessary distinction. The original baseline rationale for 3–4 is unknown.

**Failure mode considered:** silently coercing rank 3 to rank 2 or silently increasing component count. The final generator instead rejects only the explicitly declared impossible joint request and honors every other advertised tuple exactly.

## Exact input axes

**Decision:** expose only observable, strict axes:

- `grid_h`: 10–12
- `grid_w`: 11–13
- `n_components`: 2–3
- `rank`: 1–3, conditional on component count
- `component_color`: 4–9

Unknown keys and non-integer/bool integer overrides are rejected. `observe_overrides(grid)` reconstructs all five axes from pixels.

**Rationale:** these ranges cover every canonical canvas, rank, and component count while keeping placement reliable. Colors 4–9 avoid collision with the rank values 1–3 and make the legend/object roles visually distinct.

**Rejected alternatives:** permissive `**overrides` swallowing, approximate axes, hidden coercion, and advertising texture/density controls that cannot be recovered from an output grid. Those patterns caused the baseline override failure.

## Shape and schedule distribution

**Decision:** use translation-normalized fixed polyominoes of 3–8 cells, with an explicit compact table of supported bounding-box areas. For each `(n_components, rank)`, enumerate many strictly increasing cell-count schedules whose distinct bbox-area order selects a different object at that rank.

**Rationale:** cell count is the intended ranking feature; bbox area is a plausible canonical-fitting shortcut. Making the two rankings disagree in every sample gives each generated item positive semantic data value. Enumerating many schedules also prevents the rank marker from becoming an absolute-size lookup.

**Why the compact bbox table is explicit:** recomputing all fixed size-9 polyominoes in every isolated checker subprocess was unnecessary and expensive. The table only names realizable compact `(cell_count, bbox_area)` pairs; `_shapes_with_bbox` still materializes and verifies an actual shape.

**Rejected alternatives:**

1. Fixed schedules such as one selected size per rank. A new regression proved that shortcut and forced the v2.1.0 schedule expansion (`checks/tdd-red-absolute-size.log`).
2. Random walks without a finite catalog. They made exact reproducibility and bbox-area control harder.
3. Requiring every object to be non-rectangular. Canonical data contains a lawful solid selected rectangle, so this would be a validator defect.
4. Allowing bbox ties. Ties make the rival's ordering dependent on incidental traversal order rather than a clean semantic disagreement.

## Placement and determinism

**Decision:** place chosen shapes with deterministic keyed RNG and randomized backtracking, reserving `(0,0)` for the rank marker and enforcing one-cell 4-neighbor separation.

**Rationale:** separation makes component extraction unambiguous; backtracking avoids rejection-heavy sampling; sorting every set-derived catalog before keyed choices makes pixels independent of `PYTHONHASHSEED`.

**Probe:** the independent audit regenerated every one of 1,000 crossed samples and observed zero nondeterministic outputs and zero component/override observation mismatches.

## Difficulty bands

**Decision:** difficulty changes only the default canvas draw:

- easy: height 10–11, width 11–12
- medium/default: height 10–12, width 11–13
- hard: height 11–12, width 12–13

Exact overrides retain the full advertised range in every band.

**Rationale:** this produces distinct band distributions without changing the rule, component semantics, or legal override domain. An earlier version made all bands byte-identical and failed the diversity check.

**Limitation:** this is modest geometric difficulty, not a claim that hard examples demand qualitatively deeper reasoning.

## Validator and canonical support

**Decision:** `self_check` validates the true input contract—rectangular integer grid, isolated rank, 2–3 same-color separated components, distinct cell counts, legal rank—and not a preferred texture. `strict_canonical_like` checks the declared profile without demanding the synthetic bbox-rival witness.

**Rationale:** all canonical inputs must remain accepted even though the canonical set does not itself distinguish cell count from bbox area. Requiring the teaching witness in the canonical validator would incorrectly reject the authority examples.

## Lesson assembly and semantic contract

**Decision:** use 4 demonstrations plus 1 query. Declare the bbox-area rule through `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`; require every lesson and every held-out rotation to refute it.

**Rationale:** the rival fits all 5 canonical pairs, so merely producing Racket-correct labels is insufficient. Four demonstrations provide repeated varied schedules without overloading small grids, and the query is not position-dependent because each of the five pair positions was tested as holdout.

**Measured support:** `checks/lesson-census.json` materialized 100 lessons per band. All 300 production lessons and all 1,500 rotations were non-ambiguous against the declared rival, with no materialization, hook, or scoring errors.

**Limitation:** this is finite declared-rival evidence. It does not prove unique induction against undeclared hypotheses or all cyclic lesson starts.

## Tests and reusable tooling

**Decision:** retain task tests under `tests/test_generator.py` and the independent probe under `workspace/review_probe.py`.

The 40 tests cover canonical acceptance and parity, exact axes, unknown keys, incompatibility declarations, determinism, difficulty variation, semantic witnesses, bbox-rival disagreement, lesson hooks, and the absolute-size-lookup regression. The probe intentionally reimplements component analysis and both solvers instead of importing private generator helpers, and its `--racket` mode requires the real packet authority.

## Approval boundary

This repair does not set catalog approval, train safety, or training admission. Those remain maintainer decisions. No shared source, unrelated generator, base solution, or canonical row was changed.
