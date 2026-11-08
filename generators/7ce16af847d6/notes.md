# Working notes: 7ce16af847d6

## Review repair

The imported `2.0.1` source was a fixed five-component fixture.  It advertised
nine controls while honoring only dimensions in part, silently accepted unknown
keys, generated a three-color palette although every canonical input has four,
and had no executable teaching contract.  Its own degenerate textures could
also fail `self_check`.

Version `3.0.0` retains the canonical Racket rule and replaces the fixture with
a canonical-scale component grammar.  Only the observable `scene_profile` axis
is public.  The three-profile schedule supplies concrete counterexamples to
size-only, bbox-only, contains-window, color-agnostic, and recolor-all-blue
rivals in every three-example lesson.  The task-local tests and independent
workspace probe are the source-bound regression evidence.
## Current reviewer considerations

Source SHA-256: `840d6764e216ccf40dc3d61a5fc8f4d465966940c8cb182ca6c54db520f31e2a`.

# Decisions — `7ce16af847d6`

All decisions below concern generator SHA-256 `840d6764e216ccf40dc3d61a5fc8f4d465966940c8cb182ca6c54db520f31e2a`. The canonical Racket authority was not changed.

## D1 — Preserve the Racket rule

**Choice.** Keep the canonical rule and pin `RULE_HASH=a7803abc6931`.

**Rationale.** The rule is internally coherent, reproduces all five canonical outputs, and the baseline defect was distributional/contractual rather than an authority error. The final rule-smoke and authority-sync stages pass.

**Alternative rejected.** Changing the rule to match the baseline fixture would institutionalize overfitting and alter a correct canonical task.

**Failure mode checked.** Python mirror drift or input mutation. Canonical-pair tests, purity tests, rule smoke, Racket lint, and authority sync cover this.

## D2 — Replace nine advertised controls with one real axis

**Choice.** Expose only `scene_profile ∈ {canonical_mix, shape_counterexamples, color_counterexample}`.

**Rationale.** The old metadata advertised dimensions, counts, palette controls, position bias, and textures that were singleton, ignored, partially honored, or incompatible with the fixed layout. A small exact API is more useful than a broad fictional one. `observe_overrides()` can recover the selected profile from the returned grid, and unknown keys fail loudly.

**Alternative rejected.** Repairing every legacy axis. Most would add combinatorial complexity without improving the rule boundary; singleton controls such as “always two solids” are not meaningful axes.

**Probe.** Final override gate passes; task tests exercise every profile in every band and reject invalid/unknown values.

## D3 — Stay on the canonical size and palette manifold

**Choice.** Generate only 11×11 or 12×12 inputs with exactly four colors: background 0, blue 1, and two distinct non-3 decoration colors. Color 3 remains output-only.

**Rationale.** Every canonical input has one of those two dimensions and palette cardinality four. The baseline generated three-color scenes and scored 0/60 on the canonical profile floor.

**Alternative rejected.** Wider 9–16 dimensions and arbitrary palette sizes. They add off-manifold variation before the core predicate is reliably taught.

**Probe.** Profile floor and strict profile pass in every band; independent audit reports 900/900 canonical-profile hits.

## D4 — Use a constructive component grammar, not rejection placement

**Choice.** Build normalized connected shapes, assign them to separated 3–4-cell slots with deterministic backtracking, jitter inside slots, then apply a random D4 transform.

**Rationale.** This guarantees no accidental same-color contact, no overlap, and exact component identities while retaining positional/orientation diversity. It also avoids a retry loop that can silently emit fewer requested objects.

**Alternative rejected.** Randomly paint objects until they fit. That approach makes count guarantees probabilistic and complicates override observability and debugging.

**Probe.** 900 independent draws had zero self-check failures and 900 distinct inputs; component counts were always 7 or 8.

## D5 — Make every three-example lesson teach the full conjunction

**Choice.** Schedule three profiles over every three consecutive sample indices:

1. `canonical_mix` refutes recolor-all-blue.
2. `shape_counterexamples` refutes blue-size-nine, blue-bbox-3×3, and contains-solid-3×3.
3. `color_counterexample` refutes any-color-exact-3×3.

**Rationale.** The rule is the conjunction of color, size, height, and width. Each tempting single-predicate deletion receives a concrete negative witness.

**Alternative rejected.** Pure random profile selection. It can produce complete lessons with no color or shape counterexample even when aggregate witness frequency looks healthy.

**Probe.** The production lesson census reports 0 ambiguous of 300 lessons; the task-local probe checks all affordable cyclic starts for its deterministic schedule.

## D6 — Use positive targets plus lawful near-misses, not empty/degenerate lessons

**Choice.** Every generated scene contains 2–3 true targets, 2–3 blue non-target components, and two nonblue decorations.

**Rationale.** Each example demonstrates an actual transformation while simultaneously showing preserved controls. This is more useful training data than `no_solids`, `all_solids`, or blank/invalid scenes.

**Alternative rejected.** Keep the baseline degenerate textures. Some failed its own self-check, and a lesson containing only nonfiring objects teaches less about the output operation.

**Probe.** Self-check and mutation fixtures reject blank, ragged, output-color-in-input, missing-decoration, and damaged-target cases.

## D7 — Key layout randomness by difficulty without inventing fake difficulty semantics

**Choice.** Include the difficulty band in the layout RNG label. Keep the same rule and profile support in all bands.

**Rationale.** `GenCtx.draw_rng()` does not include difficulty in its salt. The first replacement therefore produced byte-identical easy/medium/hard outputs for a fixed seed/profile; a failing regression caught this. Band-keying creates independent curricula while avoiding arbitrary “hard means larger” semantics not supported by the task.

**Alternative rejected.** Leave bands identical, or make difficulty alter the predicate. The former is a dead axis; the latter changes what is being taught.

**Probe.** `checks/task-tests-dead-band-red/` records the failure; final test `test_difficulty_bands_are_not_dead` passes for all profiles.

## D8 — Keep an independent probe in the task workspace

**Choice.** Add `workspace/reference_probe.py` with its own same-color four-connected component implementation, intended-output oracle, profile observer, canonical check, distribution census, and cyclic lesson audit.

**Rationale.** Reusing generator helpers can make a test repeat the same bug. The workspace tool gives future agents a small source-bound way to challenge the generator without reading private labels.

**Alternative rejected.** Rely only on the official battery. The battery is necessary, but its lesson smoke sample and declared-rival checks do not rotate every affordable deterministic window.

**Probe.** `checks/independent-after.json` is bound to both generator and probe SHA-256 values.

## D9 — Declare finite rivals and limitations explicitly

**Choice.** Encode five plausible rivals and five witnesses, and make `lesson_identifiable()` validate visible labels and reject any rival surviving the demonstrations. Do not claim uniqueness beyond that finite set.

**Rationale.** This turns “the examples look varied” into an executable training contract while preserving epistemic honesty.

**Alternative rejected.** Claim universal identifiability from aggregate diversity or from two solver guesses.

**Limitations.** Generated scenes use 7–8 components although `self_check()` also accepts the canonical 6-component case. The grammar does not enumerate every connected shape or every possible wrong program. A future expansion should add new witnesses only when it preserves the guaranteed three-example teaching coverage.

## Parametric reviewer build — `bridge_centers`

The reviewed `3.0.0` base generator and canonical program were preserved byte-for-byte.  A native two-setting family now lives in `workspace/parametric/`: `canonical` runs the selected Racket source exactly, while `bridge_centers` first applies the canonical recoloring and then treats the newly created color-3 components as ordered waypoints.  It connects adjacent waypoint centers in reading order with horizontal-then-vertical color-3 paths.  Because generated inputs exclude color 3, the waypoint set exists only after stage A.

The family retains 2–6 demonstrations, 1–4 independently requested queries, four distinct private queries in the authoring preflight, matched inputs across settings, and substantive scenes through 30×30.  A protected skip-A program sees no waypoints and changes the witness answer.  The bounded audit covered 32 seeds, 64 setting episodes, 192 matched pairs, 192 causal separations, and 224 named-rival checks.  The authoring preflight, protected witness replay, and 16-view sequential public projection passed.  These are reviewer-side source-bound checks only: owner integration, native qualification, acceptance, variant approval, and training admission remain pending.
