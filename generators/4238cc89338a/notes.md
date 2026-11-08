# Working notes: 4238cc89338a

## Intended rule

The input has one blue (1) object and one red (2) object. Within the blue bounding box, count blue cells in each row to get `B`; within the red bounding box, count red cells in each column to get `R`. Return a `len(B) × len(R)` grid with 8 at `(r, c)` exactly when `c < B[r]` and `r < R[c]`, otherwise 0.

The canonical Racket authority was not changed. The generator pins `RULE_HASH = "e8d6ce4b7903"` and was checked for selected-authority exact sync and execution parity.

## Current generator contract (version 3.0.0)

- Rectangular 10–22 by 14–22 input over colors 0, 1, and 2.
- Exactly one 4-connected blue object and one 4-connected red object.
- Each object has exactly 5–9 cells; a one-cell moat separates them.
- Exact overrides: `grid_h`, `grid_w`, `blue_size`, `red_size`, `profile_mode`.
- Strict rejection of unknown axes, invalid scalar types, negative sample indices, and unknown difficulty names.
- `profile_mode=compact` uses row-convex blue shapes; `counterexample` includes an internal blue-row gap.
- Three ordered demonstrations. Even ordinary sample indices are counterexamples, so every three-consecutive-sample lesson refutes the declared row-span rival.
- Canonical canvas profiles 10×18 and 11×20 are deliberately scheduled in every band.
- The declared grammar has an exact 39-output codomain; the standard output-coverage schedule reaches all 39.

## Shortcut finding and retained witness

The strongest simple shortcut found is to use each blue row's occupied horizontal span instead of its cell count. It fits both canonical training demonstrations, though the canonical held-out test already refutes it. The generated counterexample at `counterexamples/review-45e724af4ac6c562-v0001/` has intended output `[[8,8,0],[8,8,0]]` and rival output `[[8,8,8],[8,8,0]]`; independent Python and selected Racket outputs agree.

## Decision reversals

1. **Placement cache removed.** An initial implementation cached all legal blue/red placement pairs. The exhaustive override audit exhausted the worker. Placement is now constructed in constant memory; the 41,670-draw matrix passes.
2. **No public lesson period.** A public `LESSON_SCHEDULE_PERIOD = 10` was considered, then removed. The ten-slot pattern is an implementation detail, not a consumer contract. `workspace/schedule_probe.py` exhausts all current residues for seeds 0–9 and three bands without making a public guarantee.
3. **Rival classification corrected.** The row-span hypothesis was initially described too strongly. It fits canonical training demonstrations, not every canonical labeled pair, so it is a lesson competitor/semantic rival rather than a canonical-equivalent rule.

## Verification summary

- Portable task tests: 32 passed.
- Override matrix: 41,670/41,670 accepted, 463 cases, zero findings.
- Semantic gate: canonical 3/3; witness 1/1; rival 1/1; 12/12 lessons; 0/48 diagnostic rotation ambiguities.
- Large census: 300/300 materialized production lessons with 0 ambiguities; 0/1,200 required-rotation ambiguities.
- Current-residue probe: 300 lessons, zero failures.
- All 12 battery-equivalent child stages pass directly on final source.

## Known limits / open findings

- Colors and semantic roles are fixed; unsupported palette permutations were not invented.
- Shapes are from a controlled connected library with sizes 5–9, not all lawful objects.
- Only the declared row-span rival and shared generic rivals were tested; this is not proof against all hypotheses.
- Output variety is intentionally finite, so output uniqueness is lower than input uniqueness.
- The unchanged canonical Racket source has one nonblocking `dummy-let-binding` style warning.
- Shared `run_generator_battery.sh` hangs after a successful single-stage child reports PASS; direct reports are retained and this is filed in `FEEDBACK_TO_CODEX.md`.
## Current reviewer considerations

Source SHA-256: `8d06cde59e6271f2218dd6472039b3a57cd8c79829b0a421f8091fd0a89fa838`.

# Decisions for 4238cc89338a

## D1 — Preserve and pin the canonical authority

**Choice.** Keep the Racket rule and canonical data unchanged, and pin `RULE_HASH = "e8d6ce4b7903"` in the generator.

**Rationale.** Canonical training and test pairs already validate the rule. The authority-sync checker confirms that the canonical program and selected task rule are exactly synchronized and behaviorally correct.

**Rejected alternative.** Editing the rule to make the generator easier to implement. No rule defect was found, and changing authority would increase review risk without improving the task.

**Evidence.** `checks/final-refresh/authority_sync.json`, `checks/final-refresh/rule_smoke.json`.

## D2 — Use a conservative explicit input grammar

**Choice.** Generate exactly one 4-connected blue object and one 4-connected red object, separated by a one-cell moat, on a rectangular grid over colors 0, 1, and 2. Each object has 5–9 cells.

**Rationale.** This directly matches the semantic decomposition exercised by the canonical rule while allowing variation in position, reflection, object size, bounding-box shape, canvas size, and output signature. The moat keeps extraction unambiguous and makes validation local.

**Rejected alternatives.** Multiple same-color objects and palette permutations were not added. Their role semantics are not established by the canonical task, and adding them would require a new authority-backed definition rather than a generator-only guess.

**Known limit.** This grammar is intentionally narrower than all conceivable lawful grids. It is a documented training distribution, not a claim that other inputs are invalid for the abstract rule.

## D3 — Replace fictional metadata with five exact controls

**Choice.** Advertise only `grid_h`, `grid_w`, `blue_size`, `red_size`, and `profile_mode`; make each exact and observable in returned pixels.

**Rationale.** The baseline's `palette_size`, `position_bias`, and textures were singleton or behaviorally dead. Exact controls are more useful to future agents and allow the shared override checker to prove the contract.

**Rejected alternative.** Keeping old labels as compatibility aliases. That would preserve a misleading API and make “accepted” overrides indistinguishable from ignored ones.

**Evidence.** 41,670 accepted draws across 463 exhaustive contract cases with zero findings in `checks/final-refresh/override_results.json`.

## D4 — Validate calls strictly

**Choice.** Reject unknown axes, invalid difficulty names, negative sample indices, and non-exact integer types, including booleans and floats.

**Rationale.** Silent coercion made the old API difficult to reason about and triggered 30 strict-scalar warnings. A strict boundary makes generator behavior reproducible and catches authoring mistakes immediately.

**Evidence.** Focused tests in `repo/generators/4238cc89338a/tests/test_generator.py`; 0 strict defect findings in `checks/final-refresh/defect_lint.log`.

## D5 — Teach counts, not occupied spans

**Choice.** Define two profile branches. `compact` uses row-convex blue shapes. `counterexample` uses a connected blue shape with a missing top-middle cell, so the row count is 2 but its occupied span is 3.

**Rationale.** “Use the blue row's occupied span” is the strongest simple shortcut found that fits both public canonical training demonstrations. A generated internal gap makes the distinction visible in the label. All red recipes have a nonempty third column, ensuring the gap affects the output.

**Correction to an earlier label.** The row-span rule was initially treated as if it fit every canonical pair. It fits the two canonical training demonstrations, but the canonical held-out test pair already refutes it. It is therefore declared as a `LESSON_COMPETITOR` and semantic rival, not as a rule equivalent on all canonical data.

**Evidence.** `repo/generators/4238cc89338a/counterexamples/review-45e724af4ac6c562-v0001/counterexample.json`.

## D6 — Use three ordered demonstrations

**Choice.** `EXAMPLES_NEEDED = 3`; ordinary even sample indices are counterexamples and odd indices are compact. The production lesson is three ordered demonstrations followed by one query.

**Rationale.** Any three consecutive samples contain at least one gapped blue row, so the declared row-span rival cannot fit all demonstrations. Three examples also matches the existing reviewer lesson floor and avoids relying on one lucky example.

**Rotation policy.** Production is ordered, but required query-rotation evidence was also collected. A 300-lesson census found no ambiguity in either production order or any of the 1,200 hold-one-out rotations.

**Evidence.** `checks/final-lesson-census.json`, `checks/final-schedule-probe2.json`.

## D7 — Guarantee canonical canvas support without collapsing size variety

**Choice.** Slots 0 and 2 use 10×18, slot 1 uses 11×20, and later slots draw from band-specific size ranges. Exact overrides always take precedence.

**Rationale.** The baseline had no canonical-size hits. Scheduling canonical profiles ensures support in every difficulty band while later slots preserve broader 10–22 by 14–22 coverage.

**Rejected alternative.** Sampling all sizes uniformly. In the small profile-floor window this can miss both canonical profiles and makes support probabilistic rather than intentional.

**Evidence.** 19/60 exact profile hits and every band supported in `checks/final-refresh/profile_floor.json`.

## D8 — Make finite output diversity explicit

**Choice.** Deduplicate shape recipes by their derived output and declare `EXPECTED_OUTPUT_CODOMAIN = 39`. The normal output-coverage schedule reaches all 39 states in the linter's standard probe.

**Rationale.** Output matrices are small and necessarily repeat. Declaring the exact codomain is more truthful than warning vaguely about low uniqueness, while input placement and reflection retain high visual diversity.

**Known limit.** The finite catalog does not approximate an open-ended object-shape distribution. It is a controlled curriculum designed around the task semantics.

**Evidence.** `checks/final-refresh/lint.log`, `checks/final-refresh/diversity.log`.

## D9 — Construct placements in constant memory

**Prior choice.** Materialize and cache every legal pair of blue and red placements for a canvas and recipe.

**New choice.** Draw a blue placement directly, compute its one-cell moat, and select a red placement from lawful rows/columns without building the Cartesian product.

**Reason for reversal.** The exhaustive override audit repeatedly generates many canvas/shape combinations. The cached-pair implementation exhausted the worker. The constructive implementation completed the full 41,670-draw audit and a separate 10,000-draw validation benchmark while preserving semantics.

**Evidence.** `checks/final-refresh/override_results.json`; regression `test_placement_is_constructive_without_materialized_pair_cache`.

## D10 — Keep the ten-slot schedule private to the implementation

**Prior choice.** Consider declaring `LESSON_SCHEDULE_PERIOD = 10` as a public contract.

**New choice.** Keep `_SCHEDULE_PERIOD = 10` private and provide a task-local exhaustive probe instead.

**Reason for reversal.** A public period declaration asks shared census tooling to treat the schedule as a supported external contract. The ten-slot pattern is useful implementation evidence but not needed by consumers and should remain changeable. `schedule_probe.py` still exhausts all current start residues across seeds 0–9 and all three bands.

**Evidence.** `checks/final-schedule-probe2.json`; test asserts no public `LESSON_SCHEDULE_PERIOD` is exposed.

## D11 — Separate label authority from reviewer oracles

**Choice.** Keep `workspace/reference_probe.py` as an independent Python mirror and verify the retained counterexample separately with `arcpuzzles apply` against the selected canonical Racket rule.

**Rationale.** The Python probe is useful for fast property tests, but it is not the label authority. Agreement between the independent implementation and the canonical runtime provides stronger evidence than testing a generator against itself.

**Evidence.** `counterexamples/review-45e724af4ac6c562-v0001/racket.json`, `checks/final-refresh/rule_smoke.json`.

## Remaining limitations

- Fixed semantic colors 0/1/2 and fixed output color 8 are intentional.
- Only object sizes 5–9 and the declared connected-shape library are generated.
- The one declared task-specific rival is not an exhaustive hypothesis class.
- The task-local ten-slot audit covers seeds 0–9, not all integer seeds.
- The canonical Racket source retains one nonblocking `dummy-let-binding` style warning; it was not changed because authority behavior is correct.
- The shared aggregate battery wrapper does not terminate after successful single-stage execution; direct stage evidence is used instead.
