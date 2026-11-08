# Working notes: bf53d21ff9fc

## Intended rule

Visit gray `5` markers in row-major order. Using the original input, select the first adjacent green `3` in up/down/left/right priority and trace the nonbranching green route with the same priority while excluding the immediately previous cell. For trails of at least two cells, apply cumulative output edits: turn the original marker and traversed route orange `7`, restore the final route cell green `3`, and place gray `5` on the penultimate route cell. Preserve inactive markers, dormant green components, zeros, and unrelated cells.

## Current repair decisions

- Version 3.1.0; `RULE_HASH` and canonical Racket behavior are unchanged.
- `seed` and `sample_index` must be literal integers; `sample_index` must be nonnegative.
- `scene_profile` remains the only public semantic axis. Every fourth default sample draws from a profile-compatible general domain and uses a canonical-scale canvas; compatibility is selected before the keyed draw, never by replacing a recorded value. Forced overrides retain the full profile domain.
- The semantic contract checks canonical acceptance, endpoint-versus-penultimate landing, route consumption, multiple active markers, inactive marker preservation, and dormant route preservation. Declared rivals are `endpoint_landing` and `preserve_route`.
- Selected base `target_code` is byte-exact with canonical `program_solution`; archival `raw_code` remains unchanged.
- Task tests use portable `reviewer_support` path helpers.

## Evidence and limits

Final generator SHA-256: `0963426cb0d3b170019a6ab67f4c32175d849ee42d81821f412f3af087a8b7ce`.

- 109 task tests pass: `checks/task-tests-after-5/result.json`.
- Strict battery is 12/12 green: `checks/after-final/checks/bf53d21ff9fc_after_battery_summary.json`.
- Profile support is 26/60 exact and 28/60 envelope; diversity is 100% unique inputs and 99% unique outputs over 300 pairs.
- The 300-lesson census found 0 production ambiguities and 0/1,200 ambiguous query rotations against the two declared rivals, with 1,199 unique inputs.

Finite rivals and samples do not prove universal identifiability. The calibrated domain excludes branching/cyclic active routes. The task-local `landing_offset` values 2 and 3 are a proposed episode-level prototype only; offset 3 is not production-approved.
## Current reviewer considerations

Source SHA-256: `0963426cb0d3b170019a6ab67f4c32175d849ee42d81821f412f3af087a8b7ce`.

# Decisions: bf53d21ff9fc

## D1 — Preserve the canonical transformation

**Choice.** Keep the existing rule mirror and pinned `RULE_HASH`; repair contracts, schedule coverage, and authority synchronization around it.

**Rationale.** Baseline rule smoke and execution parity were already green, canonical labels agreed, and the associated note described the same input-pure row-major route transformation. Rewriting a correct rule would add risk without addressing the measured failures.

**Alternatives rejected.** Replacing the generator with only canonical examples would trivially improve exact-profile support but destroy diversity. Changing route traversal or Racket semantics was rejected because no semantic defect was reproduced.

**Probe and failure mode.** Final rule smoke, canonical task tests, and authority execution parity bind the unchanged behavior. Remaining uncertainty is limited to inputs outside the calibrated nonbranching route domain.

## D2 — Enforce literal scalar contracts at the public entry point

**Choice.** Require `type(seed) is int`, `type(sample_index) is int`, and `sample_index >= 0` before constructing generator context.

**Rationale.** Python booleans are integers by subclassing, so `isinstance(value, int)` would still admit `True` and `False`. The baseline defect linter reproduced 33 invalid acceptances across difficulty bands.

**Alternatives rejected.** Silent coercion (`int(value)`) would collapse distinct caller mistakes into valid seeds and make provenance unreliable. Allowing negative indices was rejected because the authoring API and strict checker treat them as invalid.

**Probe and failure mode.** Focused tests enumerate booleans, floats, strings, `None`, and negative `sample_index`; valid literal integers remain deterministic.

## D3 — Increase canonical support without post-draw substitution

**Choice.** On every fourth default sample, choose a compatible general-profile domain before the keyed `scene_profile` draw and use a canonical-scale square canvas from 9, 12, 13, or 14. Forced overrides use the full profile domain.

**Rationale.** The baseline had zero exact-profile support in medium and hard. The first repair tried replacing the drawn profile afterward; the override checker correctly found 21/90 provenance mismatches. Selecting the feasible domain first preserves the declared keyed value.

**Alternatives rejected.** Hardcoding public examples on a large fraction of samples would overfit and reduce generalization. Clamping or replacing a drawn profile was rejected because it makes metadata disagree with the returned grid. Applying anchors to forced overrides was rejected after it broke legal public-profile requests.

**Probe and failure mode.** The final profile floor is 26/60 exact and 28/60 envelope, every band has support, the override matrix is 810/810 green, and diversity remains 100% unique inputs/99% unique outputs. The schedule is finite and does not prove every legal joint configuration is equally represented.

## D4 — Declare a falsifiable semantic teaching contract

**Choice.** Add strict-domain acceptance, two named rivals (`endpoint_landing`, `preserve_route`), two direct semantic witnesses, and branch witnesses for multiple active markers, inactive markers, and dormant routes.

**Rationale.** Correct labels alone do not show that demonstrations distinguish the intended rule. These rivals are directly plausible from the canonical examples and executable against generated lessons.

**Alternatives rejected.** A prose-only `EXAMPLES_NEEDED` declaration would not verify lesson identifiability. Adding many speculative rivals without task evidence would create noise and brittle false alarms.

**Probe and failure mode.** The final semantic gate fires all five witnesses, verifies both rivals, and finds no ambiguity in 12 smoke lessons or 300 census lessons with 1,200 rotations. Undeclared plausible rules remain an explicit limit.

## D5 — Synchronize selected authority text while preserving archival evidence

**Choice.** Set base `target_code` byte-for-byte equal to canonical `program_solution`; leave `raw_code` unchanged.

**Rationale.** The baseline authority check showed active selected authorities diverged only in exact text while execution parity passed. The return guide treats canonical plus selected target as active authority and archival raw text as historical evidence.

**Alternatives rejected.** Reformatting canonical source would unnecessarily change the ledger. Replacing archival raw text would erase provenance. Ignoring the exact mismatch would leave the strict after gate red.

**Probe and failure mode.** Final authority sync reports selected sources synchronized, one intentional archival divergence, and execution parity across two distinct source texts.

## D6 — Make task tests portable

**Choice.** Resolve repository/canonical paths through `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`.

**Rationale.** Fixed `parents[...]` assumptions passed only in the authoring tree and failed in staged runtime before reaching the new assertions.

**Alternatives rejected.** Relaxing or skipping the portable preflight would conceal a real handoff defect. Copying canonical data into tests would create stale duplicate authority.

**Probe and failure mode.** The inherited preflight failure is retained at `checks/tdd-red/`; final staged task tests pass 109/109.

## D7 — Keep the parametric variant separate from canonical production

**Choice.** Prototype `landing_offset` with allowed values 2 and 3, selected once per episode. Offset 2 is the canonical default; offset 3 moves gray to the antepenultimate route cell. Require active routes of length at least three.

**Rationale.** The parameter changes one interpretable decision in the Racket rule while preserving all other mechanics. It yields distinguishable labels and supports hidden episode-level induction.

**Alternatives rejected.** Per-example parameter sampling would make a lesson internally inconsistent. Exposing the parameter in public JSON would leak the answer. Varying traversal priority or route-consumption behavior was rejected because those changes entangle multiple semantics and make calibration harder.

**Probe and failure mode.** The prototype executes both instantiated Racket programs, proves canonical parity for offset 2, and produces a settings witness. Only two settings and two retained episodes were exercised; offset 3 is not approved for production.

## D8 — Treat audit targets as read-only

**Choice.** Reproduce concrete findings for both drawn targets and do not patch either source.

**Rationale.** The assignment explicitly separates adversarial audits from the selected repair. Source-bound reproducers and official receipts are sufficient for intake.

**Alternatives rejected.** Opportunistic fixes would exceed the permitted patch scope and blur repair versus audit conclusions.
