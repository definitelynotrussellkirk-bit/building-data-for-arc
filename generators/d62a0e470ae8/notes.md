# Working notes: d62a0e470ae8

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `ec7545cf16e4e43fe7bdc944b4799d6773ced15f4db69c34bb2db37ee84a07dd`.

# Design decisions for `d62a0e470ae8`

## D1 — Treat the selected canonical row as the authority

**Choice.** Keep the Racket rule unchanged, pin `RULE_HASH = "43fde3a5fa41"`, and make generator semantics conform to it.

**Rationale.** All four canonical pairs execute correctly, authority synchronization passes, and the defect was in generated inputs and metadata rather than labels. The authority defines exactly four meaningful key branches: clockwise, left-right reflection, top-bottom reflection, and 180° rotation.

**Alternatives rejected.** Extending the rule to keys `5..7` would invent task semantics and require a shared authority edit. Retaining keys `5..7` as identity would teach a misleading seven-way dispatch and produce invisible branch duplicates.

**Probe/failure mode.** Canonical Python mirror and Racket parity are checked in `workspace/reference_probe.py`; 4/4 canonical pairs and 28/28 parity cases pass in `checks/reference-probe-final.json`.

## D2 — Replace generic metadata with four exact observable controls

**Choice.** Advertise only `grid_profile`, `key`, `main_size`, and `n_distractors`.

**Rationale.** Each value can be reconstructed from pixels by `observe_overrides`; all legal combinations are constructively supported. This removes dead `palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture` claims.

**Alternatives rejected.** Keeping generic axes as aliases would preserve a larger apparent combinatorial reach but not real controllability. Keeping negative fixtures as `texture` values would mix invalid teaching examples into the ordinary product domain.

**Probe/failure mode.** The override gate exhausts advertised values and combinations, rejects unknown keys, and is green in `checks/after/checks/d62a0e470ae8_after_override_results.json`. Invalid types, out-of-range values, unknown axes, and unsupported difficulty labels have direct tests.

## D3 — Use six grid profiles with canonical-heavy support

**Choice.** Support `7x9`, `8x10`, `9x9`, `9x11`, `10x12`, and `11x13`; include the three exact canonical profiles in every band’s schedule.

**Rationale.** The first three recover real-task dimensions and three-color palettes. The larger three provide placement freedom for distractors and output-shape diversity without changing the rule.

**Alternatives rejected.** Difficulty-specific dimension ranges caused exact overrides to be accepted in metadata but silently clipped or ignored in some bands. Fully unconstrained height/width pairs would enlarge the state space while creating many impossible shape/distractor combinations.

**Probe/failure mode.** Profile floor records 29 exact canonical-profile hits over 60 draws, with nonzero support in all bands (`checks/after/checks/d62a0e470ae8_after_profile_floor.json`).

## D4 — Make “largest object” causal with same-color distractors

**Choice.** Generate one unique largest component and `0..3` strictly smaller same-color components, all outside the main bounding box and mutually four-disconnected.

**Rationale.** Same-color distractors directly exercise the authority’s same-color component decomposition and size selector. Keeping them outside the main bounding box distinguishes “crop the selected object” from “crop all foreground.” The foreground remains one color, preserving the canonical three-color profile: background, key, object.

**Alternatives rejected.** Different-color distractors can be discarded by a color heuristic. Distractors inside the main bounding box do not refute an all-foreground crop if they happen to lie in empty cells. Equal-size components make the authority’s tie behavior underdetermined for a learner. A permanent distractor requirement would remove the zero-distractor canonical regime.

**Probe/failure mode.** `include_all_objects` and `select_smallest` are refuted in every one of 300 production lessons; individual distractor witnesses appear in 332/480 independent draws.

## D5 — Use asymmetric main shapes with full dihedral orbits

**Choice.** Keep three connected templates for each size `5..9`, randomized over eight orientations, and require every selected key to change the crop.

**Rationale.** A full orbit prevents a symmetric shape from making a branch observationally identical. Multiple templates and orientations provide output variety while bounded constructive placement avoids rejection instability.

**Alternatives rejected.** Random grown blobs can accidentally be symmetric or rectangular, making transformations invisible. Rejection-only generation can fail unpredictably under exact profile/size/distractor combinations. A single template per size would make size a strong shape-class shortcut.

**Probe/failure mode.** Self-check verifies unique-largest structure and transform visibility. The independent 480-draw probe reports 480 unique inputs and zero self-check errors.

## D6 — Preserve short-window coverage without locking axes together

**Choice.** Derive an independent deterministic seed offset for each scheduled axis, then advance each by `sample_index` modulo its own cardinality.

**Rationale.** Four consecutive examples still cover all keys and distractor counts, but different seeds change their relative phase. This makes compact lessons reliable without allowing one axis to become a proxy for another.

**Rejected first draft.** Direct schedules `key = 1 + sample_index mod 4` and `n_distractors = sample_index mod 4` were perfectly correlated. The independent gate exposed this after 90 tests were green. The added regression failed in `checks/tdd_schedule_red.log` before the schedule was repaired.

**Limitation.** Deterministic marginal schedules can still have higher-order correlations with profile and main size. Tests cover pairwise key/distractor unlocking and production lesson rival rejection, not every statistical dependency.

## D7 — Let difficulty vary incidental pixels, not legal exact domains

**Choice.** Every exact control remains legal for `easy`, `medium`, and `hard`; difficulty selects separate deterministic RNG streams for template, color, orientation, and placement.

**Rationale.** This satisfies the framework’s band calls without inventing a false semantic ordering. It also prevents exact override failures caused by band-specific bounds.

**Rejected first draft.** Reusing the same RNG labels across bands made all three difficulties pixel-identical under fixed exact axes. A red regression required at least 20/24 sampled triplets to differ; the final implementation passes while preserving observed axes.

**Limitation.** Difficulty is nuisance diversity, not measured reasoning complexity. This is stated rather than overstated.

## D8 — Require four demonstrations and executable rival rejection

**Choice.** Set `EXAMPLES_NEEDED = 4`, declare five semantic rivals and witnesses, and implement `lesson_identifiable`.

**Rationale.** Four examples can cover all four key branches and all four distractor-count residues. The competitor set targets the main plausible shortcuts: ignore dispatch, fixed transform, all-foreground crop, wrong size selector, and omitted key-4 branch.

**Alternatives rejected.** Two or three demonstrations cannot guarantee all four key meanings. Witness-frequency-only checks do not establish that each complete lesson rejects every rival.

**Probe/failure mode.** The source-bound lesson census materialized 100 lessons per band. All five rivals were refuted in every lesson, with zero ambiguity, hook warning, or scoring error (`checks/lesson-census.json`).

## D9 — Keep an independent oracle and reusable probe beside the task

**Choice.** Add `workspace/reference_probe.py` rather than relying only on production helpers.

**Rationale.** It independently parses components, crops, applies transformations, observes axes, measures distribution and rival disagreement, checks canonical pairs, and optionally verifies live Racket parity. Future agents can replay it without reconstructing the analysis.

**Alternative rejected.** Testing `rule_mirror` against itself would only prove internal consistency. The probe has separate implementations for the authority rule and object analysis.

**Limitation.** The parity helper is intended for packet/reviewer environments with the bundled Racket runtime; ordinary generator import and tests do not require Racket.

## D10 — Synchronize human-facing summary, but leave unrelated audit tasks untouched

**Choice.** Update selected-task `SUMMARY.md` to v3.0.0 and document audit findings only in `AUDIT.md`/`checks/audit`.

**Rationale.** A stale summary would continue to teach maintainers the old seven-key contract even though code and tests were correct. The two audit targets were findings-only by assignment, so modifying them would violate scope.
