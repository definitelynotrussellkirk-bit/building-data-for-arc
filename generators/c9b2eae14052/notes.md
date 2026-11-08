# Working notes: c9b2eae14052

## Review finding — palette diversity concealed fixed geometry

The version-2.0.0 generator passed the full 12-stage baseline battery, including the existing diversity stage, but seed variation changed only object colors. For each of 36 `(difficulty, schedule_profile)` strata (three bands × twelve profiles), the same public axes and the same occupied-cell layout recurred across all 12 pinned seeds. The task-local color-blind probe measured exactly **1 unique input geometry out of 12** in every stratum (432 total draws), even though the generic diversity stage reported 97% unique colored inputs. Evidence: `checks/custom/geometry_diversity_before.json` and `checks/before/checks/c9b2eae14052_before_diversity.log`.

This is a training-data defect rather than a rule defect: a learner could overfit a tiny location/template vocabulary while the palette made the dataset look diverse. The selected canonical Racket authority and `RULE_HASH=83a03df6b45f` were already correct and were not changed.

## Repair — version 2.1.0

The fixed slot table was replaced with deterministic seed-keyed constrained packing:

- enumerate all translation-normalized connected polyominoes of sizes 2–4;
- enumerate every placement whose actual border-contact set exactly matches its semantic slot (interior, one specified side, or one specified corner);
- shuffle candidate lists with the generator context's `object_geometry` RNG;
- use exhaustive backtracking, placing the most constrained object first, while preserving no overlap and no orthogonal contact;
- rotate two-border negatives through northwest, northeast, southeast, and southwest instead of only northwest/southeast;
- preserve the existing 12-profile semantic schedule, public axes, canonical anchors, colors, and Racket rule.

The candidate enumerations are cached by `(slot, size, height, width)`. The domain is small (`height 8..14`, `width 7..14`, sizes 2..4), so the cache is bounded and the backtracking search remained fast in stress testing.

## Test-first record

A new regression test, `tests/test_geometry_diversity.py`, was written before the repair. It requires at least six unique color-blind layouts across 12 seeds for every band/profile stratum while holding observed public axes constant.

- RED: all three parametrized band tests failed immediately at profile 0 because the baseline produced `1 >= 6` false. Evidence: `checks/custom/geometry_diversity_red.log`.
- GREEN: the same test passed after the repair. Evidence: `checks/custom/geometry_diversity_green.log`.
- Portable task suite: 13/13 task-local tests passed in a generated runtime layout. Evidence: `checks/custom/portable_task_tests.log`.

## Final measurements

Final generator SHA-256: `eabe4c07ccc507e4e27d90a43d735aef25c2b07bb0b63899926ade0ca92615ea`.

- Geometry probe: every one of the 36 strata produced 12/12 distinct color-blind input layouts across seeds 12000–12011; minimum/median/maximum were 12/12/12. Evidence: `checks/custom/geometry_diversity_after.json`.
- Full-axis packing stress: 2,400/2,400 deterministic random override draws succeeded; all four one-border sides and all four corners occurred; 2,190 distinct component-shape multisets were observed. Probe seed `20261002`. Evidence: `checks/custom/packing_stress.json`.
- Generic diversity: 300 generated pairs improved from 97% to 100% unique colored inputs and from 62% to 92% unique outputs. Evidence: before/after diversity logs.
- Full after battery: 12/12 stages green; strict semantic support 600/600; all eight witness/rival claims held in 60/60 checked cases each; 12/12 three-demo lessons were identifiable; canonical profile support remained 27/60 exact and 35/60 in-envelope. Evidence: `checks/after/`.

## Reusable task-local tools

- `workspace/geometry_diversity_probe.py`: source-hash-pinned, palette-insensitive geometry census over bands/profiles/seeds.
- `workspace/packing_stress_probe.py`: deterministic full-axis generation, validation, semantic-side/corner coverage, and shape-multiset stress test.
- `workspace/portable_task_tests.py`: builds the actual portable package layout in a temporary directory and runs all task-local pytest files.

## Remaining limitations

The geometry threshold (six unique layouts per 12 seeds) is intentionally task-specific; a globally applied gate needs an opt-out for tasks whose semantics require a finite fixed layout vocabulary. The repository-wide source test suite has one unrelated reproducible failure in `tests/test_review_runtime.py::test_streaming_timeout_retains_progress_and_stops_child` (captured stdout is empty under a 0.2-second timeout); it failed twice, while 143 other tests passed and 28 Racket-dependent tests were skipped in that direct run. The selected task's portable suite and complete Racket battery are green.
## Current reviewer considerations

Source SHA-256: `eabe4c07ccc507e4e27d90a43d735aef25c2b07bb0b63899926ade0ca92615ea`.

# Decisions for `c9b2eae14052`

Final generator SHA-256: `eabe4c07ccc507e4e27d90a43d735aef25c2b07bb0b63899926ade0ca92615ea`.

## D1 / `FND-1`: Repair geometry, not the rule or lesson schedule

**Input choice.** Preserve the existing public axes (`grid_h`, `grid_w`, `n_objects`), 12-profile semantic schedule, difficulty mapping, colors, object-size range, and exact-one-border rule; vary the object geometry and placement within those constraints.

**Original rationale.** The exact rationale for the fixed coordinate table was not recorded. It plausibly guaranteed small-canvas feasibility, object isolation, deterministic semantics, and canonical-like examples, but that is an inference rather than documented intent.

**Alternatives considered.** Increasing palette permutations was rejected because it was the source of the misleading diversity signal. Changing the Racket rule or profile schedule was rejected because the semantic battery, canonical pairs, rival witnesses, and authority sync were already sound. Changing dimensions by seed was rejected because schedule-profile comparisons should hold public axes constant and because dimension churn can mask layout repetition just as colors did.

**Probe and result.** `geometry_diversity_probe.py` bins colors and stratifies by band/profile while confirming constant observed axes. It measured 1/12 layouts in every baseline stratum and 12/12 in every final stratum.

**Failure modes and limits.** A generator with intentionally finite, semantically meaningful templates can legitimately have low color-blind diversity. The proposed general gate therefore needs an explicit finite-vocabulary declaration or opt-out rather than a global hard threshold.

## D2 / `FND-1`: Use all fixed polyominoes of sizes 2–4

**Input choice.** Enumerate translation-normalized, orthogonally connected fixed polyominoes for each requested size in the pre-existing `2..4` range.

**Original rationale.** The baseline used only a few bars, Ls, and squares. No rationale was documented for excluding the other legal connected shapes.

**Alternatives considered.** Random walks were simpler but can heavily bias shape frequency and generate duplicates. A hand-written larger shape list would improve variety but remain incomplete and easy to regress. Free polyomino canonicalization under rotation/reflection was rejected because orientation itself is useful geometric variety; fixed polyominoes retain each orientation.

**Probe and result.** The 2,400-draw stress probe observed 2,190 distinct complete component-shape multisets while all generated scenes passed the validator.

**Failure modes and limits.** Enumeration is deliberately capped at size 4. Raising the object-size axis substantially would cause combinatorial growth and should trigger either a different sampler or bounded shape catalog.

## D3 / `FND-1`: Define placement by exact border-contact sets

**Input choice.** A candidate placement is legal only when the object’s observed side set exactly equals its requested slot: `{}` for interior, `{top|right|bottom|left}` for a positive target, or one of the four two-side corner sets for a multi-border negative.

**Original rationale.** The baseline slot names encoded this intent indirectly through fixed coordinates. Exact-contact semantics were already the core rule and validator invariant.

**Alternatives considered.** Sampling a coordinate and repairing it afterward was rejected because it can accidentally add a second border contact. Sampling anywhere and classifying after the fact was rejected because it can alter the requested teaching schedule. Restricting edge objects to straight bars was rejected because it would keep shape/location shortcuts.

**Probe and result.** The full-axis stress tool calls the public `generate()` path, then `self_check()` and `observe_overrides()`. It completed 2,400/2,400 legal draws with no override mismatch and observed every one-border side.

**Failure modes and limits.** Candidate generation assumes rectangular grids and orthogonal connectivity, matching this task. It should not be generalized unchanged to diagonal-connectivity or nonrectangular tasks.

## D4 / `FND-1`: Backtrack under no-touch constraints rather than greedily falling back

**Input choice.** Shuffle legal candidates with a dedicated deterministic RNG and solve the placement problem by backtracking, always selecting the most constrained remaining object. Maintain no overlap and no orthogonal contact between distinct same/different-color objects.

**Original rationale.** The baseline’s fixed slots guaranteed separation. The validator’s connected-component semantics require separation so adjacent different-color objects do not become ambiguous under generic nonzero-component analyses.

**Alternatives considered.** First-fit greedy placement was rejected because unlucky early choices can falsely report an impossible scene at minimum dimensions. Silent size/slot fallback was rejected because it would violate the declared schedule and weaken witness guarantees. Allowing orthogonal contact and relying on color separation was rejected because some supporting analysis treats all nonzero neighbors as connected and because it creates avoidable shortcut ambiguity.

**Probe and result.** No packing exception occurred in 2,400 randomized draws spanning every legal value of all three public axes. The complete standard override and grammar stages are also green.

**Failure modes and limits.** Backtracking is exponential in principle. The candidate cache and small domain kept it fast here; any future increase in object count, grid size, or shape size should be accompanied by a runtime budget test.

## D5 / `FND-1`: Rotate multi-border negatives through all four corners

**Input choice.** Use northwest, northeast, southeast, and southwest corner slots rather than only northwest and southeast.

**Original rationale.** No rationale was documented for the two-corner restriction; it likely simplified fixed-coordinate packing.

**Alternatives considered.** Retaining two corners would leave an avoidable positional shortcut. Sampling arbitrary objects that happen to touch two borders was rejected because rectangular connected objects can only do so near a corner and exact corner identity is easy to schedule directly.

**Probe and result.** The stress census observed northeast 884 times, northwest 921, southeast 871, and southwest 884, with no missing corner.

**Failure modes and limits.** Counts are coverage evidence, not a formal uniformity test. Uniform corner frequency is not semantically required, but severe skew should remain visible in the report.

## D6 / `FND-1`: Isolate geometry randomness in `object_geometry`

**Input choice.** Derive candidate shuffling from `ctx.draw_rng("object_geometry")`, leaving palette and other streams independent.

**Original rationale.** The runtime’s named RNG streams exist to make dimensions independently replayable; the baseline did not need a geometry stream because geometry was fixed.

**Alternatives considered.** Reusing palette RNG was rejected because changes to color sampling would perturb geometry and make regressions harder to localize. Global `random` was rejected because it would break deterministic generation.

**Probe and result.** Both task-local probes are deterministic and source-hashed. The after battery’s reproducibility, override, and grammar checks are green.

**Failure modes and limits.** Exact samples can change if candidate enumeration order changes, even with the same seed. The semantic contract and distribution probes—not byte-identical historical samples—are the intended stability target.

## D7 / `FND-1`: Add a thresholded regression test plus richer diagnostic probes

**Input choice.** The unit regression requires at least 6 unique binary layouts from 12 pinned seeds for every one of 36 strata and requires observed axes to remain constant. The richer probe records input/output binary uniqueness and shape-multiset uniqueness without making all of those diagnostics hard test assertions.

**Original rationale.** The standard generic gate measured colored grids globally, which allowed palette changes to hide fixed geometry. There was no task-local geometry gate.

**Alternatives considered.** Requiring 12/12 in the unit test was rejected as unnecessarily brittle even though the final source currently achieves it. A global unstratified uniqueness percentage was rejected because variation in dimensions/profiles can conceal a dead stratum. Requiring shape-multiset uniqueness alone was rejected because identical shapes at varied positions are also useful and should count as layout diversity.

**Probe and result.** The new test failed before implementation (`1 >= 6` false in all three bands) and passed afterward. The final diagnostic census is 12/12 in all 36 strata.

**Failure modes and limits.** The pinned seed window can miss rare collapse modes. The 2,400-draw stress probe broadens coverage, while the small deterministic unit window keeps routine tests cheap.

## D8: Keep authority and canonical data unchanged

**Input choice.** No edit to the canonical JSONL or Racket source.

**Original rationale.** Canonical behavior already implements the intended exact-one-border rule, and all canonical outputs matched authoritative execution.

**Alternatives considered.** None justified by evidence. A distribution defect should not be “fixed” by changing the target rule.

**Probe and result.** Racket lint, rule smoke, canonical profile floor, authority sync, and 600/600 strict semantic cases all pass on final source. `RULE_HASH` remains `83a03df6b45f`.

**Failure modes and limits.** The archival bank remains reported as divergent by authority sync exactly as it was before; the selected authority is synchronized and execution parity passes.

## D9 / `AUD-1` and `AUD-2`: Return audit reproducers without editing audit targets

**Input choice.** Build standalone, hash-checking Python probes that execute each target’s authoritative Racket rule and save the counterexample plus census to JSON.

**Original rationale.** The assignment explicitly requires adversarial review but no fix, and source edits are permitted only under the selected task.

**Alternatives considered.** Prose-only suspicions were rejected because both issues could be directly reproduced. Patching the audit targets was rejected as out of scope.

**Probe and result.** `68e9f92d8e4b`: the rival fit 120/120 generated cases while 4/5 canonical pairs were rejected by the target self-check. `0083f06314c3`: the color-1 shortcut fit 240/240 generated cases and 3/3 canonical pairs, then failed a validator-accepted color-1 mutation.

**Failure modes and limits.** These probes establish concrete coverage/validator defects, not the best repair design for those generators. Maintainers should separately decide whether to broaden generation, repair component extraction, or narrow documented domains.

## D10 / `ENV-1`: Do not repair unrelated repository infrastructure

**Input choice.** Record the reproducible streaming-timeout failure and leave repository helpers unchanged.

**Original rationale.** Source scope is restricted to the selected generator, and the failure does not affect its Racket-backed battery or portable task tests.

**Alternatives considered.** Editing `review_runtime.py` or relaxing its test was rejected as an unauthorized unrelated change.

**Probe and result.** The full source suite reported 1 failure, 143 passes, and 28 skips. The same test failed alone with the same missing stdout.

**Failure modes and limits.** This environment failure may be timing/platform sensitive, but the immediate isolated replay reproduced it. It remains a maintainer follow-up rather than a blocker for `FND-1`.
