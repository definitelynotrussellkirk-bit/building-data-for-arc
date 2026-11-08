# Working notes: f8d1d470d522

## Current rule and authority

Color 8 is walkable unless cardinally adjacent to color 7. The two color-9 markers remain walkable. Choose a legal path by minimum length, then minimum direction changes, require the optimum to be unique, and paint that path color 9. Unused 8 branches and all 7 cells remain unchanged.

Selected generator version: `3.1.0`; SHA-256 `7b1f01594dd2b7f0d47276e0ba2afee6fcc06cce6c5f3be1844ef9fc8d04b236`. Canonical Racket `RULE_HASH=f1588fca855d` was not changed. The two selected `target_code` mirrors were synchronized to canonical text; archival `raw_code` remains historical.

## Decisions now in force

- API calls require exact integer `seed` and nonnegative exact integer `sample_index`; bools are rejected.
- Public axis: `selection_mode = unique_shortest | fewest_turns`. Explicit overrides bypass curriculum scheduling and must be observed exactly.
- Default sampling uses a five-position cycle: semantic anchor A, exact canonical profile A, semantic anchor B, exact canonical profile B, general scene.
- Semantic anchors are generated route graphs with causal obstacles and an equal-length tie whose unique fewest-turn route wins. Vertical orientations prevent shared first/topmost-object explanations.
- Exact-profile draws retain all four complete canonical morphologies under lawful D4 transforms and padding; they are 2/5 of default samples, not the whole distribution.
- Declared executable rivals: ignore obstacles, prefer most turns among shortest paths, and prefer the bottommost shortest path. `bottommost_shortest` fits all canonical pairs and has a retained generated counterexample.
- Lessons use five demos and one query. Every cyclic schedule start and every query rotation must refute all declared rivals.

## Reversed choices

The earlier stochastic exact-profile prior (about 12%) was replaced by the deterministic schedule because random pooled support did not guarantee a teachable complete lesson. An intermediate horizontal anchor schedule was replaced with vertical anchors after exact rotations admitted generic `first/topmost object only` rules; the failing receipts are retained under `checks/task-tests-generic-red/` and `checks/semantic-required/`.

## Measured final evidence

- Battery: 12/12 green, no advisory/failure (`checks/after-final-green/`).
- Focused tests: 19 tests and 123 subtests passed (`checks/task-tests-final/`).
- Profile floor: exact/envelope 23/60; every band supported.
- Semantic gate: 600/600 strict, 8/8 canonical, all named witnesses/rivals valid, 0/90 fixed-schedule rotation ambiguities.
- Large census: 300/300 lessons and 1,800/1,800 rotations identifiable against declared rivals; 1,145 unique inputs.
- Final exposed solve: 5/5 visible examples on attempt 1, bound to the final generator SHA.

## Native parametric family

`workspace/parametric/` now implements the native adapter contract for episode-level `turn_preference = fewest | most`. `fewest` remains byte-for-byte canonical/default. The adapter supports 2–6 demos and exactly four private queries, uses setting-neutral distinguishing inputs, and retains a substantive 30×30 query. The replayable protected-Racket self-audit covers both settings, seeds 0/17, demo boundaries 2/6, five cheap bypasses, and an additional 24-seed generation sweep. Native qualification and owner acceptance remain separate gates.

## Known limits / open findings

Finite declared-rival testing is not a proof of unique human induction. Exact-profile slots draw from a finite canonical morphology family. The parametric audit covers two finite settings and bounded seeds/rivals; it does not establish learning benefit or training admission. No blocking finding remains for the selected production repair; audit-only findings for other tasks are in `AUDIT.md` and were not patched.
## Current reviewer considerations

Source SHA-256: `7b1f01594dd2b7f0d47276e0ba2afee6fcc06cce6c5f3be1844ef9fc8d04b236`.

# DECISIONS — f8d1d470d522

## D1: Preserve the canonical rule and repair the generator around it

**Input choice.** The canonical family contains four unique public scene morphologies (duplicated across selected training/augmented authorities) and two real decision modes: a unique shortest route and an equal-length shortest-path tie resolved by fewest turns.

**Original rationale.** The baseline summary already described shortest path followed by fewest turns. The exact history behind the existing implementation was not available, so any deeper original rationale is unknown.

**Decision.** Keep the canonical Racket rule byte-for-byte and keep `turn_preference="fewest"` as production behavior. Repair generation, validation, teaching support, and selected text mirrors instead of changing the law.

**Alternatives rejected.** Replacing the task with a simpler single-corridor construction would lose the branching-network reasoning. Changing the tie-break to a positional route would fit the canonical examples but encode the wrong abstraction.

**Probe/evidence.** All 8 canonical labeled pairs match an independent path enumerator, the generator mirror, and the selected Racket authority. See `checks/after-final-green/checks/f8d1d470d522_after_rule_smoke.json` and the focused tests.

**Limits/failure modes.** The rule assumes one uniquely optimal fewest-turn path. Structural impostors or unresolved ties are rejected by `self_check` rather than assigned arbitrary labels.

## D2: Develop a small parametric extension first, but isolate it

**Input choice.** Parameterize only the secondary decision: `turn_preference ∈ {fewest, most}` among already-shortest legal routes. The canonical/default value is `fewest`.

**Rationale.** This changes one compositional decision while preserving marker roles, obstacle adjacency, shortest-path search, output palette, and route painting. It is small enough for demonstrations to distinguish without creating a different task family.

**Alternatives rejected.** Parameterizing obstacle behavior (“respect/ignore 7”) would weaken the defining causal relation. Parameterizing shortest versus longest route would alter the core search objective and often require different graph domains. Palette parameters would test symbol binding rather than the intended route reasoning.

**Implementation.** `workspace/parametric/prototype.py` chooses the setting once from the episode seed, builds two demos and one query on shared fewest-turn-tie inputs, and emits setting-specific Racket programs and redacted public examples.

**Probe/evidence.** At seed 19 both settings match all three Racket executions and every demo refutes the other setting: `checks/parametric/turn-preference-seed19-final.json`.

**Limits.** This is a proposed prototype, not production approval. It covers two settings at one retained seed and the opposite-setting rival only; undeclared rivals remain untested.

## D3: Enforce exact scalar API semantics

**Prior choice.** The baseline accepted Python integer-like values loosely and did not reject negative `sample_index`; the original reason is unknown.

**Decision.** Require `type(seed) is int`, `type(sample_index) is int`, reject bools, and require `sample_index >= 0`. Validate difficulty and override names/values before any RNG use.

**Why.** Negative indices and booleans undermine deterministic replay and violated the strict-scalar detector. Validation at the API boundary fixes the source rather than special-casing downstream failures.

**Alternatives rejected.** Coercing strings/floats or silently clamping negatives would create multiple recipes for one instance and conceal caller bugs.

**Probe/evidence.** The baseline defect was reproduced; final regressions cover negative indices, booleans, floats, unknown controls, and removed controls. Final task tests and lint are green.

## D4: Replace a probabilistic profile prior with a deterministic five-position schedule

**Prior choice.** An intermediate implementation used an approximately 12% random exact-profile branch. It could satisfy pooled support in expectation but did not guarantee a complete lesson’s morphology or semantic evidence.

**Decision.** Use the repeating schedule:

1. `semantic_anchor_a`
2. `canonical_profile_a`
3. `semantic_anchor_b`
4. `canonical_profile_b`
5. `general`

The schedule applies only to default sampling; an explicit `selection_mode` override bypasses it.

**Why.** Every consecutive five-demo lesson receives two exact canonical-profile inputs, two generated semantic anchors, and one general scene. The policy is transparent, testable for all cyclic starts, and exceeds the profile floor without flooding the distribution with copied shapes.

**Alternatives rejected.** Pure random mixing made lesson guarantees statistical rather than structural. All-profile lessons would overfit four finite morphologies. All-general lessons initially missed exact profile support.

**Probe/evidence.** Final profile support is 23/60, with 8/20, 7/20, and 8/20 exact hits by band. The long focused prior check measures 230–250 exact-profile draws per 600 and at least 400 distinct input/output pairs.

**Limits.** Exact-profile slots draw from a finite source family under lawful D4 transforms and padding. They are intentionally only 2/5 of the schedule.

## D5: Use two independent semantic anchors, not one copied witness

**Decision.** Generate two anchor families with equal-length shortest alternatives and a unique fewest-turn winner, plus causal color-7 blocking. The anchors use vertical D4 orientations `(1, 3)`.

**Reason.** An intermediate schedule passed named route rivals but two rotations still admitted generic “first/topmost object only” explanations. A retained failing regression identified the exact starts. Vertical anchors break shared positional attribution while preserving the route law.

**Alternatives rejected.** Merely adding more copies of one anchor would increase frequency without increasing explanatory diversity. Filtering the offending rotations would hide the curriculum defect and restrict downstream query placement.

**Probe/evidence.** `checks/task-tests-generic-red/` and `checks/semantic-required/` preserve the failures. `checks/task-tests-final/`, `checks/semantic-required-final/`, and the 300-lesson census show the repair.

**Limits.** The generic mutation set is targeted, not exhaustive. Unknown object-selection shortcuts may exist outside the tested family.

## D6: Declare rivals by semantic role and retain executable witnesses

**Decision.** Retain three deterministic rivals:

- `ignore_obstacles`: shortest/fewest-turn path when color 7 has no disabling effect.
- `most_turns_shortest`: among shortest legal routes, prefer the most turns.
- `bottommost_shortest`: among shortest legal routes, maximize path row-sum instead of minimizing turns.

`bottommost_shortest` is also `CANONICAL_SHORTCUTS` because it fits all 8 canonical labeled pairs. Each witness is source-bound and executable; lesson identification checks complete demos, not only individual labels.

**Why.** These alternatives separately challenge the obstacle law, the tie-break direction, and a strong positional shortcut that the public examples do not rule out.

**Alternatives rejected.** Identity/flip/rotation baselines are useful generic diagnostics but are not the strongest family-specific rival. A string-only rival declaration would not verify predictions.

**Probe/evidence.** Semantic gate: 600/600 strict draws, 3/3 witness definitions, 3/3 rival claims, 12/12 sampled lessons, 0/72 sampled rotation ambiguities, and 0/90 fixed-schedule rotation ambiguities. The large census reports 0/300 production ambiguities and 0/1,800 rotation ambiguities.

**Limits.** Passing a finite rival set does not establish universal induction.

## D7: Keep forced overrides exact and separate from lesson scheduling

**Decision.** Preserve only the meaningful public axis `selection_mode ∈ {unique_shortest, fewest_turns}`. Explicit overrides call the requested builder directly and report the observed mode exactly.

**Why.** A hidden schedule must not override a caller’s exact control. Removed or unsupported controls should fail loudly rather than be accepted but ignored.

**Alternatives rejected.** Treating the schedule profile as a public override would expose curriculum mechanics as task semantics. Keeping deprecated controls would expand the API without a verified behavioral contract.

**Probe/evidence.** Final override stage accepted 270/270 cases; focused tests verify every forced value and rejection path.

## D8: Synchronize selected authority text without rewriting archival source

**Finding.** Two selected `target_code` fields differed textually from the canonical program even though execution parity passed.

**Decision.** Copy the canonical program into selected `target_code` in:

- `repo/shared/data/base/solutions/training/cc9053aa__f8d1d470d522.json`
- `repo/shared/data/base/solutions/augmented/cc9053aa__5d750b933294.json`

Leave archival `raw_code` unchanged.

**Why.** Selected authority should be exact and reviewable, while archival capture must remain historical evidence.

**Alternatives rejected.** Changing the canonical rule was unnecessary. Rewriting `raw_code` would destroy provenance. Waiving text mismatch because outputs agree would leave future sync checks ambiguous.

**Probe/evidence.** Final authority-sync stage is green and records selected synchronization, archival divergence, and execution parity.

## D9: Make tests portable rather than patching the frozen fixture

**Finding.** The selected task tests hard-coded repository depth and failed in the isolated portable runtime before exercising behavior.

**Decision.** Resolve roots and canonical data through `reviewer_support.find_root`, `canonical_path`, and `load_selected_generator`. Keep new tests under the selected task’s `tests/` directory; do not edit the frozen baseline root fixture.

**Why.** The same test must run in repository and staged runtime layouts. Source-relative parent guesses are not a portable contract.

**Probe/evidence.** Portable preflight then final task run complete with 19 tests and 123 subtests.

## D10: Preserve failed iterations and source-bound solve history

**Decision.** Retain the baseline failures, generic-spatial red regression, initial semantic warning, interrupted battery receipts, and first non-disagreeing shortcut probe. When generator bytes changed after an earlier 5/5 solve, move that entire solve to `checks/prior-solve/` and prepare a new final-source episode.

**Why.** A later pass does not erase the evidence that motivated the change, and a solve cannot be rebound to new generator bytes by copying it.

**Evidence.** Final solve generator hash equals `7b1f01594dd2b7f0d47276e0ba2afee6fcc06cce6c5f3be1844ef9fc8d04b236`; its first attempt passes 5/5 visible examples. Prior solve evidence remains under `checks/prior-solve/`.

## D11: Compression policy for large census evidence

**Decision.** Keep the compact census summary uncompressed and transport the 22 MiB full report as deterministic gzip with a mapping manifest containing original path, size, SHA-256, compressed path, compressed size/SHA, and restoration command.

**Why.** The return has a 25 MiB expanded evidence budget. The summary is enough for routine review; the compressed full report preserves every materialized lesson and replay recipe.

**Limit.** Consumers must restore the JSON before tools expecting the original filename can read it.
