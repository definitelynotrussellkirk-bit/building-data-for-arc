# Working notes: e706449ebf4c

## Current intended rule

Find each 4-connected red (`2`) component. Treat every generated component as a
straight bar, measure its inclusive bounding-box length, and locate its midpoint
in doubled coordinates. Paint cyan (`8`) into cells whose doubled-coordinate
Manhattan distance from that midpoint is at most the bar length, but only when
the evolving output cell is zero. Preserve every red cell, union overlapping
auras, clip at the canvas boundary, and keep the input shape.

The selected canonical Racket program was not changed. Its normalized
`RULE_HASH` remains `665e4af22561`; the exact canonical expression SHA-256 is
`665e4af2256108582659b7dceaa73dd4f546fb6e9b73738f1ff7cea22159a8c7`.

## Review lead and baseline

I used current associated note `GNOTE-000222` as a design and distribution lead.
It accurately described the accepted aura semantics and prior diversity work.
There was no task-local prior return indexed as an unresolved repair lead.

The selected baseline generator SHA-256 was
`8948d170e1959e88caa9e5acfa94dd871f95ac6f5a82c07c1ad9bc49c834fffb`.
The before battery completed with 10 green stages, one semantic advisory, and
one hard failure. `defect_lint` reproduced acceptance of nonliteral/negative
call scalars; `semantic_gate` reported no executable lesson-rival contract.
Evidence: `checks/before/`.

## Final repair decisions

1. **Fail closed on call scalars.** `generate` now requires `type(seed) is int`,
   `type(sample_index) is int`, and a nonnegative sample index. This rejects
   booleans, floats, strings, and negative indices before context construction.
2. **Make the teaching contract executable.** Two plausible rivals are declared:
   `integer_center_radius` floors even-bar half-cell centers and uses an integer
   radius; `overwrite_other_red` incorrectly lets one aura erase a neighboring
   red bar. The associated witnesses are doubled-midpoint geometry and red-bar
   preservation.
3. **Make complete four-pair lessons rotation-safe against both rivals.** In the
   default schedule, every even sample index is an `aura_hits_other_bar` scene.
   That scene uses an even bar length, so it is a joint witness. Every four
   consecutive draws therefore contain two joint witnesses; holding out any one
   pair leaves at least one decisive demonstration.
4. **Restore canonical-profile support without replaying public grids.** One
   joint witness in each four-draw block uses a randomly generated scene on a
   canonical canvas shape. Geometry, orientation, length, placement, and output
   remain newly sampled. This repaired the hard-band profile-floor regression
   introduced by the stronger lesson schedule.
5. **Keep explicit overrides literal.** A requested `scene_profile` bypasses the
   default teaching schedule and is generated exactly. The observable override
   contract remains `{"scene_profile": ...}`.
6. **Repair task-test portability.** The inherited test used a fixed parent-depth
   path that failed in the isolated task runtime. It now uses
   `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`.

Final selected generator SHA-256:
`1f13d3755c0fcf003cdcd6f8df54123dff8da0d2b671b027890d6e318b6a036b`.

## Verification

- Final after battery: all 12 stages green in `checks/after-final/`.
- Portable task tests: 30 tests and 10 subtests passed in
  `checks/task-tests-profile-floor-green/`.
- Required-rotation semantic gate: 12/12 production lessons identifiable and
  0/48 ambiguous rotations in `checks/semantic-rotations-final/`.
- Source-bound census: 300/300 lessons materialized, 1,200 pairs, 1,200 query
  rotations, zero production or rotation ambiguities, and 1,136 unique inputs.
  Summary and compressed full report are in `checks/lesson-census-final.*`.
- Profile floor: 21/60 exact canonical-profile hits and 28/60 envelope hits,
  with support in easy, medium, and hard, in `checks/profile-floor-green/`.
- The post-repair visible-only solve passed 3/3 examples on its first checked
  revision and is bound to the final generator hash in `solve/summary.json`.

## Parametric prototype

`workspace/parametric/` contains a proposed, unapproved `radius_delta` extension.
Allowed values are `{0, 2}` in doubled Manhattan-distance units. `0` is the exact
canonical/default rule; `2` expands the aura by one grid cell while preserving
bar extraction, inclusive length, doubled midpoint, zero-only painting, clipping,
overlap, and red preservation. The setting is selected once per episode.

Bounded evidence in `checks/parametric/radius-delta-final/` exercises both
settings over two episodes (six demonstrations and two queries), checks all six
canonical pairs under the default, executes 24 Racket evaluations, and reports
zero ambiguities against the alternative parameter setting. This prototype is
not a production API change and does not carry variant approval.

## Limits and open questions

The rival and census results are finite evidence against the declared hypotheses,
not a proof of unique induction against every possible program. The default
schedule deliberately overweights the interaction profile to make short lessons
teachable; explicit profile overrides and the full distribution/diversity gates
still pass, but downstream consumers should retain that curriculum choice rather
than reinterpret it as an unbiased scene-frequency estimate. No task-local
battery failures remain on the final source.
## Current reviewer considerations

Source SHA-256: `1f13d3755c0fcf003cdcd6f8df54123dff8da0d2b671b027890d6e318b6a036b`.

# Decisions: e706449ebf4c

## D1 — Preserve the canonical rule and repair the generator contract only

- **Prior choice:** The associated accepted note `GNOTE-000222` and selected
  Racket authority define doubled-midpoint Manhattan auras around red bars.
- **Decision:** Keep the canonical Racket expression byte-identical and retain
  `RULE_HASH=665e4af22561`.
- **Why:** All canonical pairs, parity checks, and rule-smoke checks already
  supported the authority. The reproduced failures were generator API and
  curriculum defects, not label defects.
- **Alternative rejected:** Rewrite or simplify the Racket rule. This would add
  authority risk without addressing the observed failures.
- **Probe/evidence:** `checks/before/`, `checks/after-final/`, and the default
  parametric rule hash in `checks/parametric/radius-delta-final/report.json`.
- **Failure mode/limit:** Preserving authority does not prove that the natural
  language interpretation is the only plausible ARC rule.

## D2 — Reject nonliteral and negative call scalars

- **Original rationale:** Unknown; the baseline delegated all values to
  `gen_ctx`, which allowed Python booleans and other coercible values.
- **Decision:** Require literal integers for `seed` and `sample_index`, and
  require `sample_index >= 0`.
- **Alternatives considered:** Coerce strings/floats to integers; accept booleans
  as integers; validate only sample indices. All were rejected because they
  collapse distinct caller errors into reproducible but unintended draws.
- **Probe/evidence:** The before `defect_lint` failure and focused scalar tests;
  final `defect_lint` is green in `checks/after-final/`.
- **Failure mode/limit:** Negative seeds remain allowed because the shared
  contract probes seed type, not sign, and deterministic integer seeds are
  otherwise lawful.

## D3 — Declare two executable semantic rivals

- **Original rationale:** The baseline had scene diversity but no executable
  statement of what demonstrations must distinguish.
- **Decision:** Declare `integer_center_radius` and `overwrite_other_red`, with
  witnesses for half-cell midpoint geometry and preservation of a second bar.
- **Why:** Both are simple implementation shortcuts; the second is
  canonical-fitting and therefore especially relevant to training quality.
- **Alternative rejected:** Add only prose invariants. Prose cannot be scored on
  complete generated lessons or query rotations.
- **Probe/evidence:** `checks/semantic-rotations-final/` and
  `checks/lesson-census-final.*`.
- **Failure mode/limit:** Passing these rivals does not cover every plausible
  rule or every accidental model shortcut.

## D4 — Use two joint witnesses per four-pair default lesson

- **Original rationale:** Independent random profile draws can produce correct
  labels while leaving a query-changing rival consistent with all three demos.
- **Decision:** Force `aura_hits_other_bar` at every even sample index and make
  its main bar even-length. Each four-draw window contains two examples that
  jointly refute both declared rivals.
- **Alternative considered:** Exactly one forced witness per four draws. Rejected
  after the rotation-required semantic probe showed that holding out the sole
  witness can make a lesson ambiguous.
- **Alternative considered:** Force all four pairs to the interaction profile.
  Rejected as unnecessary distribution collapse.
- **Probe/evidence:** Retained RED rotation tests, then 0/48 ambiguity in
  `checks/semantic-rotations-final/` and 0/1,200 in the final census.
- **Failure mode/limit:** The schedule intentionally changes profile frequency;
  consumers should treat it as an ordered curriculum, not an unbiased sampler.

## D5 — Recover profile-floor support with canonical canvas shapes, not public replay

- **Prior choice:** The first rotation-safe schedule used ordinary band-specific
  interaction canvases.
- **Reversal:** Hard-band exact canonical-profile support became zero, caught by
  `checks/preflight-profile_floor/`.
- **New decision:** At default indices divisible by four, generate a fresh joint
  witness on a canvas shape drawn from the canonical shape set. Keep orientation,
  bar length, placement, and geometry randomized.
- **Alternative rejected:** Replay an exact public input in every block. That
  would meet the profile statistic but reduce novelty and teach less geometry.
- **Probe/evidence:** `checks/profile-floor-red/`,
  `checks/profile-floor-green/`, and final task tests.
- **Failure mode/limit:** Canvas-shape matching is deliberate support, not a claim
  that generated content follows the public input distribution.

## D6 — Build a separate `radius_delta` prototype

- **Decision:** Add a task-local, unapproved prototype with
  `radius_delta ∈ {0,2}` doubled-distance units. `0` is canonical; `2` expands
  the aura by one cell.
- **Why:** It changes the executed transformation while preserving bar roles,
  midpoint reasoning, clipping, overlap, and red preservation.
- **Alternatives rejected:** Vary only colors, canvas size, or scene weights;
  those are cosmetic/sampling changes rather than rule parameters. Vary center
  rounding; that would entangle the parameter with even-bar semantics rather
  than make one bounded threshold change.
- **Probe/evidence:** `workspace/parametric/` and
  `checks/parametric/radius-delta-final/`.
- **Failure mode/limit:** Two seeds and declared parameter rivals are bounded
  evidence only. Saturated or extremely clipped grids can make the settings
  observationally identical, so scheduled demonstrations avoid those cases.

## D7 — Make task tests portable through `reviewer_support`

- **Prior choice:** The inherited test located canonical data with a fixed
  `Path.parents[...]` depth.
- **Decision:** Use `find_root`, `canonical_path`, `canonical_pairs`, and the
  selected-generator loader where appropriate.
- **Why:** The portable task-test runtime changes source depth; the original
  test failed during collection before exercising behavior.
- **Alternative rejected:** Special-case the staged directory depth. That would
  remain brittle across repository and isolated layouts.
- **Probe/evidence:** Initial `checks/task-tests-red/` collection failure and the
  final 30-test/10-subtest pass.
- **Failure mode/limit:** This repairs this task's tests; a shared lint is still
  needed to prevent the pattern elsewhere (feedback F3).
