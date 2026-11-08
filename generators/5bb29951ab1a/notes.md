# Working notes: 5bb29951ab1a

## Baseline diagnosis

- No prior return was used as a lead; `evidence/associated_notes.jsonl` was empty.
- The imported v1.4.0 prose said positive dots need at least two orthogonal rectangle neighbors, but generation placed dots only immediately outside one solid rectangle. Such cells have at most one rectangle neighbor.
- Independent baseline probe: 120/120 scenes passed the old self-check, yet 0/778 dots exercised the authority's positive `adjacency >= 2` branch (`checks/baseline-semantic-probe.json`).
- The old self-check silently changed the threshold to `>=1`, so it certified a distribution on which every dot was removed by the Racket rule.
- The before battery had 6 green, 2 advisory, and 4 failed stages: lint, defect lint, override, and authority sync.
- Advertised texture/geometry controls were clamped, band-dependent, unobservable, or degenerate; unknown axes were accepted.

## Selected repair

- Replaced the single-rectangle construction with two to five same-color rectangles separated by one-cell gutters.
- Guaranteed at least one dot with exactly two **opposite** rectangle neighbors. Additional positive dots replace parity-separated rectangle cells that retain at least two original rectangle neighbors.
- Guaranteed both one-neighbor and isolated negative dots in every scene.
- Reduced the public surface to five exact, pixel-observable axes valid in every band: dimensions, positive count, negative count, and palette.
- Added strict validation, deterministic generation, robust malformed-input diagnostics, exact `observe_overrides`, and a pinned `RULE_HASH`.
- Declared and tested the strongest canonical-fitting rival found: absorb only dense holes or perpendicular corner notches, not straight two-sided bridges.
- Added `workspace/reference_probe.py`, including an independent Python oracle, exact shortcut witness, and fail-closed canonical Racket batch runner.

## Authority handling

The Racket behavior was not changed. Both selected task-local `target_code` fields were synchronized byte-for-byte to the existing canonical `program_solution`; the compact `raw_code` fields remain archival and execution-equivalent. Final authority status is `selected_synchronized_archival_divergent` with execution parity PASS.

## Final evidence

- Generator SHA-256: `a85c037bcfefc277e73efcd829e3d4bf2f61d4a1a38b889e5982fdcecb31d763`.
- Full after battery: 12/12 green (`checks/after-rerun/`).
- Task-local tests: 33 passed, including real Racket parity over canonical, generated, and shortcut-witness inputs (`checks/task-tests-final/`).
- Lesson census: 100/100 lessons in each band, 1,500 unique inputs, zero ambiguous lessons; all three declarations of `corner_or_dense_only` were refuted 100/100 per band (`checks/lesson-census.json`).
- Exposed visible-only solve: 4/4 demonstrations passed in one attempt; earlier rule exposure declared honestly (`solve/`).

## Limits

The generator teaches a bounded rectangular-block manifold rather than every legal arrangement of rectangle-colored cells. The census is finite and checks a declared rival family; it is not a universal proof of identifiability.
## Current reviewer considerations

Source SHA-256: `78e91c65e82aa6c376d132af33eeeb016a0640bd6776da2f008a7a6755d04e7f`.

# Decisions for `5bb29951ab1a`

## D1 — Start from the selected approved baseline

**Choice.** Use source `a85c037bcfefc277e73efcd829e3d4bf2f61d4a1a38b889e5982fdcecb31d763`
and its current notes/tests as the lead. Its review index binds it to
`review-29a0b2cf213aeda8:v0001`.

**Rationale.** The assignment explicitly pins the selected baseline. Prior claims
are leads, not measurements, so all relevant checks were rerun against current
bytes.

**Rejected alternative.** Importing an older or unintegrated patch. That would
make the measured source and returned source diverge.

## D2 — Preserve valid production semantics and Racket authority

**Choice.** Do not alter geometry, sampling, canonical Racket, `RULE_HASH`, or
`VERSION`; repair only invalid-call handling.

**Rationale.** The selected distribution already had strong branch coverage,
exact overrides, a decisive bridge witness, and approved authority binding. The
only current battery defect was an API contract failure.

**Rejected alternatives.** Refreshing the version for an invalid-input-only
change; changing the Racket rule; broad distribution refactoring unrelated to
the reproduced failure.

**Failure mode.** Any future change to valid draw bytes would require a version
and reproducibility review; this repair intentionally avoids that.

## D3 — Validate all call arguments at the boundary

**Choice.** Require exact `int` for `seed`, exact nonnegative `int` for
`sample_index`, and one of `None/easy/medium/hard` for `difficulty`, before
calling `gen_ctx`.

**Rationale.** The baseline battery first exposed invalid difficulty acceptance.
After that was fixed, the next defect-lint run revealed 33 invalid seed/index
acceptances. These are one root cause: incomplete boundary validation.

**Rejected alternatives.** Coercing strings/floats with `int`; accepting booleans
as integers; letting negative indices alias the deterministic stream; validating
only the first symptom.

**Evidence.** `checks/before/...defect_lint.log`,
`checks/after/...defect_lint.log`, final green defect lint under
`checks/after-final/`, and focused tests in `tests/test_generator.py`.

## D4 — Use one semantic parameter: orthogonal-neighbor threshold

**Choice.** Prototype `orthogonal_neighbor_threshold ∈ {1,2,3}`, selected once
per episode; default/canonical is `2`.

**Rationale.** It changes the executed transformation while preserving the
original family’s object roles, spatial relation, and reasoning steps. Each value
has meaningful positive and negative cases within the same lawful grid family.

**Rejected alternatives.** Palette changes, dimensions, rectangle count, or dot
count are sampling parameters, not rule parameters. A direction parameter or
new composition would replace the original reasoning pattern. Threshold 0 or 4
would make one branch too trivial on this family and provide weaker nearby tasks.

## D5 — Require complete support-degree witnesses in every episode

**Choice.** Retain only pairs containing degree-0, degree-1, degree-2, and at
least one degree-3/4 sparse dot; use three demonstrations and one query.

**Rationale.** This simultaneously exercises both output branches for all three
settings and guarantees threshold 1 versus 2 and threshold 2 versus 3 are visible
in demonstrations, rather than first appearing in the query.

**Rejected alternatives.** Random episodes without postselection; one witness
per whole bundle; independently resampling the threshold per pair.

**Limit.** The retained episodes are a deliberately strong teaching subset, not
an estimate of the natural frequency of every support degree.

## D6 — Derive and execute exact Racket for each setting

**Choice.** Keep threshold 2 byte-for-byte canonical and replace only the unique
comparison constant for thresholds 1 and 3. Execute every materialized input
through the included Racket bridge and compare with the independent Python
mirror.

**Rationale.** Python-only labels would not meet the authority requirement.
Limiting the textual change to one uniquely identified comparison keeps the
variant interpretable and source-reviewable.

**Failure mode.** A future canonical source that no longer contains one unique
`(>= adj 2)` causes the prototype to fail closed.

## D7 — Build a reusable, privacy-safe evidence materializer

**Choice.** `workspace/parametric/materialize.py` records production/prototype
source hashes, exact Racket/program and episode hashes, adjacency histograms,
rival witnesses, private episodes, and public stripped challenges.

**Rationale.** Future agents can regenerate and verify the same evidence with one
command. Source binding prevents stale examples from silently surviving a code
change; public stripping prevents parameter/program/query-answer leakage.

**Rejected alternative.** Hand-authored JSON examples or unbound screenshots.

## D8 — Keep failed iterations

**Choice.** Retain both failed batteries: baseline invalid difficulty and the
first repair that exposed seed/index validation.

**Rationale.** They establish the debugging path and motivate the shared-tool
feedback that argument probes should not mask one another.

## D9 — Report composition conservatively

This is a single local conditional transformation. `contextual_gating` is
**present** only in the limited sense that each dot's local orthogonal support
determines the branch; the witness is the same lesson containing degree-1 and
degree-2 dots, and the rival is a one-neighbor threshold. `multi_rule_interaction`
and `sequential_state` are not applicable. `task_defined_symbols` is present at
an episode level because color roles are inferred by frequency, but the current
optional annotation is omitted to avoid overclaiming corpus-level coverage.
