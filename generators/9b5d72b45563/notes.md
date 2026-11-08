# Current account: 9b5d72b45563

## Intended rule

On a fresh same-size color-0 canvas, scan every isolated nonzero input seed in row-major order. Paint the seed center and its four one-step diagonal neighbors in the seed color, clipping outside the grid. When two X footprints overlap, the later row-major seed overwrites the earlier paint.

The selected canonical Racket authority was not changed. Its normalized hash is pinned as `cc30c7127a64`.

## Reversed baseline decisions

The baseline forced at least one border seed, prohibited overlapping X footprints, rejected three of four canonical inputs, and exposed nine mostly dead or unobservable axes. Those choices hid a canonical overwrite case and made the advertised distribution misleading.

Version 2.0.0 replaces them with one exact, pixel-observable `scene_profile` axis and an eight-profile deterministic schedule. Four teaching profiles jointly contain four seeds, one clipped boundary seed, a repeated color, and a different-color same-row overlap. Four control profiles match every canonical height/width/palette signature. Easy/medium/hard preserve the same geometry while using distinct bijective nonzero-color relabelings, so the built-in difficulty control is not dead.

## Teaching contract

Every generated lesson uses four demonstrations plus one query candidate. In every five consecutive scheduled pairs, at least two are comprehensive teaching scenes; therefore holding out any one pair leaves at least one complete witness. The declared competitors include the three strongest canonical-fitting shortcuts (`first_two_seeds_only`, `right_to_left_within_rows`, and `first_seed_per_color`) plus boundary, center, geometry, fixed-color, and first-writer rivals.

The shared census checked 300 production lessons / 1,500 query rotations with zero ambiguity, warning, or scoring error. The task-local finite-schedule probe additionally enumerated all eight cyclic starts across 25 seeds and three bands: 600 lessons / 3,000 rotations, again with zero findings. These are finite declared-rival checks, not a proof against every imaginable hypothesis.

## Domain and limits

Inputs contain 2–4 color-0-background singleton seeds, isolated in the 8-neighborhood. X footprints may overlap even though source seeds may not be adjacent. Single-seed grids are lawful for the broad executable transformation but intentionally outside this training distribution; the validator rejects them. Grid sizes are the eight declared profile sizes, and nonzero colors remain role-interchangeable.

The exact retained shortcut witness is `counterexamples/first-two-seeds-only.json`. The reusable exhaustive probe is `workspace/cyclic_lesson_probe.py`; it reads the generator's live `LESSON_COMPETITORS` declaration rather than duplicating rival names.

## Open findings

No task-local blocker remains in the final checked source. The shared aggregate battery runner can stall between otherwise fast independent stages; individual final stage receipts are retained, and this runner issue is reported separately as tooling feedback.
## Current reviewer considerations

Source SHA-256: `67ddf6ce934a6e686395471fcbad9232afa62fa0b05fda053512cd6a30d7bd16`.

# Decisions: 9b5d72b45563

## D1 — Preserve the authority; repair the sampler

**Choice.** Keep the selected Racket rule unchanged and pin `RULE_HASH="cc30c7127a64"`.

**Baseline rationale.** Unknown. The baseline had no hash pin and encoded extra border/spacing assumptions in Python rather than in the authority.

**Alternatives considered.** Rewrite Racket to require a border seed; remove overlap semantics; keep the rule unpinned.

**Evidence.** Baseline rule smoke applied 120/120 inputs without crashes, and all canonical outputs match the final independent mirror. Final `rule_smoke`, `racket_lint`, and `authority_sync` are green.

**Failure mode / limit.** Any future authority change invalidates the pin and requires fresh parity evidence.

## D2 — Replace nine misleading controls with one exact profile axis

**Choice.** Declare only `scene_profile`, with eight dimension-unique values recoverable from returned pixels.

**Baseline rationale.** The original axis rationale was undocumented; several controls were constant, dead, or aliases for fixed distribution assumptions.

**Alternatives considered.** Keep old axes as diagnostics; expose independent seed count, boundary, overlap, palette, and size controls; let impossible combinations silently clamp.

**Evidence.** Final lint and override matrix are green. Every explicit profile is valid and exactly observable in all three bands.

**Failure mode / limit.** Dimensions identify profiles, so this is a curriculum control rather than a factorized combinatorial axis set. This is deliberate: it prevents invalid cross-products and makes every advertised value exact.

## D3 — Alternate comprehensive teaching scenes with canonical-scale controls

**Choice.** Use period eight: teaching, control, teaching, control, repeated across four teaching and four control profiles.

**Why.** Canonical examples alone admit first-two-seeds, first-seed-per-color, and ambiguous overlap-order rules. A comprehensive teaching scene refutes all three while also teaching clipping and full X geometry. Controls retain simpler canonical-scale examples and all canonical dimension/palette signatures.

**Alternatives considered.** Make every pair maximally complex; rely on random witness frequency; schedule one rare overlap example; preserve the old border-only curriculum.

**Evidence.** Shared census: 300 lessons / 1,500 rotations clean. Exhaustive schedule probe: 600 lessons / 3,000 rotations over all starts clean.

**Failure mode / limit.** The proof is against declared executable rivals. Undeclared hypotheses can still exist.

## D4 — Permit X-footprint overlap but reject adjacent source blobs

**Choice.** Source seeds must be Chebyshev-separated by at least two cells. Their painted X footprints may overlap, and row-major later-writer precedence is taught explicitly.

**Why.** Canonical input contains overlapping footprints; forbidding them erased an answer-bearing branch. Adjacent nonzero cells would instead merge the notion of “seed” with a multi-cell object and are outside this generator grammar.

**Alternatives considered.** Forbid every footprint collision; permit arbitrary adjacent source clusters; resolve overlap with first-writer semantics.

**Evidence.** Focused tests compare left-to-right and right-to-left writers on an exact same-row overlap. The live Racket output selects the later/right color.

**Failure mode / limit.** Other overlap geometries are lawful under the authority but not exhaustively factorized as separate profiles.

## D5 — Require at least two generated seeds

**Choice.** `self_check` rejects single-seed inputs, even though the broad executable transformation can handle them.

**Why.** The selected distribution and every canonical input contain at least two seeds. A singleton teaches geometry but cannot teach all-seed processing, repeated colors, or interaction order. Making it off-distribution also prevents a generic minimal-impostor warning from disguising the actual training contract.

**Alternatives considered.** Accept every authority-lawful singleton; add singleton controls; claim full executable-domain coverage.

**Evidence.** Canonical acceptance remains 4/4; every generated profile remains valid; strict defect lint is green.

**Failure mode / limit.** This is a stated training-domain restriction, not a claim that the Racket rule rejects singletons.

## D6 — Make difficulty representational, not semantic

**Choice.** Easy, medium, and hard apply different fixed bijections to nonzero colors while retaining the same profiles, witness structure, and rule complexity.

**Why.** Difficulty is part of the shared sampler API. Leaving it byte-identical triggered dead-band evidence; tying it to graph structure would make some bands semantically weaker.

**Alternatives considered.** Remove difficulty; map hard to more seeds or more overlap; use larger grids per band.

**Evidence.** A red-first regression proved the bands were identical. The final regression verifies three distinct grids with the same observed profile; strict defect lint no longer reports dead bands.

**Failure mode / limit.** This is not a calibrated monotonic cognitive-difficulty ladder.

## D7 — Declare executable rivals and lesson requirements

**Choice.** Add independent intended and rival implementations for first-two-seeds, reverse within-row order, first seed per color, ignore boundary, omit center, cardinal-plus, fixed-color, and first-writer overlap. Require four demonstrations and refute every declared rival.

**Why.** Correct labels on individual grids do not prove that a generated lesson identifies the intended rule.

**Alternatives considered.** Rely only on instance validation; list rival names without executable functions; check production query position only.

**Evidence.** Task tests verify canonical fit for the three canonical shortcuts and direct refutation in every teaching profile. Both shared and exhaustive query-rotation checks are clean.

**Failure mode / limit.** Competitor completeness is inherently open-ended.

## D8 — Build an exhaustive finite-schedule probe

**Choice.** Add `workspace/cyclic_lesson_probe.py`, which dynamically reads `LESSON_COMPETITORS`, enumerates every period residue, rotates each bundle through every query position, and binds source hashes in its report.

**Why.** The ordinary high-volume shared census intentionally samples production lessons and reports `schedule_coverage: null`. Its `--enumerate-schedule-period` mode certifies every start at one fixed seed; the task-local probe extends that exact check across 25 seeds per band while reading the live rival declarations.

**Alternatives considered.** Stop at the shared one-seed schedule enumeration; hard-code rival names in a one-off notebook; infer safety from witness frequency; increase random census size only.

**Evidence.** `checks/schedule-census-final.json`: 24 lessons / 120 rotations over every start at fixed seed `730000`, clean. `checks/cyclic-lesson-probe.json`: 600 lessons / 3,000 rotations over every start and 25 seeds per band, also clean.

**Failure mode / limit.** The tool depends on a truthful finite period declaration and still scores only live declared rivals.
