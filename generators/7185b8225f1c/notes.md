# Current notes: 7185b8225f1c

## Intended rule

Find four-neighbor-connected red (`2`) components. Red singletons stay unchanged. For every component with at least two cells, compute its full axis-aligned bounding box, expand that rectangle by one cell in all four directions, clip it to the canvas, and paint every black (`0`) cell in the expanded rectangle green (`3`). Preserve red cells; overlapping rectangles form a union.

The canonical Racket semantics and `RULE_HASH=df2d840acdd1` are unchanged. The selected training and augmented `target_code` fields were exact-text synchronized to canonical `program_solution`; archival `raw_code` was preserved.

## Repaired teaching defect

The strongest canonical-fitting shortcut found is `cell_halo_only`: for each non-singleton component, paint only the one-step Chebyshev neighborhood of each red cell. It fits all six usable labeled canonical pairs but disagrees on concave components whose expanded bounding rectangle contains an outer corner not within one step of any component cell. A minimal lawful witness and authoritative Racket output are retained in `counterexamples/cell_halo_only.json` and `checks/counterexamples/7185b8225f1c-cell-halo/`.

Version `3.1.0` replaces the prior wholly random default profile draw with a two-slot teaching schedule:

- even `sample_index`: `bbox_witness`, choosing a concave or mixed polyomino and retrying until it refutes `cell_halo_only`;
- odd `sample_index`: `broad`, retaining all thirteen public/general profiles with weighted public support.

Explicit `scene_profile` overrides bypass the teaching schedule and remain exact. Every four consecutive generated pairs therefore contains at least one witness in every three-pair demonstration rotation. `EXAMPLES_NEEDED=3`; the declarations `strict_canonical_like`, `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, and `lesson_identifiable` expose the finite semantic contract.

## Input contract

`seed` must be a literal integer (not Boolean, float, string, or `None`). `sample_index` must be a literal nonnegative integer. This closes the 33 strict-scalar warnings in the pinned baseline.

## Evidence

- Final generator SHA-256: `940518d2d0e4b3ee54487d3cc180bdf6ef1a323bd661053b503a589d17f738c0`.
- After battery: all 12 stages green (`checks/after/checks/7185b8225f1c_after_battery_summary.json`).
- Focused repair contracts: 19 passed (`checks/repair-contracts-green.log`).
- Parametric prototype tests: 12 passed (`checks/parametric/prototype-tests-green-rerun.log`).
- Lesson census: 300 lessons / 1,200 unique pairs; three demonstrations plus one query; production and all 1,200 query rotations reported `no_ambiguity_found` against the declared rival, with zero hook warnings or scoring/materialization errors (`checks/lesson-census.summary.json`).
- Post-repair visible solve: 3/3 examples passed; prior rule exposure was declared (`solve/summary.json`).

## Parametric extension (not production)

`workspace/parametric/prototype.py` proposes one episode-level parameter, `halo_radius ∈ {1,2}`. Radius 1 is exact canonical Racket source; radius 2 changes only the expansion distance. Two four-pair episodes, sixteen Racket applications, and all eight query rotations passed with the alternate radius refuted. This is bounded prototype evidence only and changes no selected rule, generator path, or approval state.

## Remaining limitation / blocker

The inherited frozen `tests/test_generator_7185b8225f1c.py` uses a fixed `Path(__file__).resolve().parents[1]` canonical-data path. Portable task-test preflight therefore stops before pytest; the fixture is frozen and was not edited. New portable tests pass directly, but aggregate task-test completion remains blocked pending maintainer migration to `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs` (`checks/task-tests/result.json`). Finite declared-rival checks do not prove uniqueness against arbitrary programs.
## Current reviewer considerations

Source SHA-256: `940518d2d0e4b3ee54487d3cc180bdf6ef1a323bd661053b503a589d17f738c0`.

# Decisions — review-703ec0b979accf43

## D1 — Treat the cell-level halo as the primary teaching rival

**Prior choice.** Version 3.0.0 generated a broad mixture of public, domino, polyomino, overlap, edge, and singleton-heavy scenes but declared no semantic contract and did not ensure that any complete lesson distinguished a full expanded bounding rectangle from the union of per-cell halos.

**Lead used.** I used prior return `review-1e0c6bcbf0642406:v0001` (source SHA-256 `1829ecd43d7650638dab38e9b73977adef24a8dd29960b1cd5ce0f09265636f9`) only as a lead. I independently verified that `cell_halo_only` fits every usable labeled canonical pair and reproduced a lawful concave counterexample with authoritative Racket output.

**Decision.** Declare `cell_halo_only` in all three finite rival namespaces and link it to witness `full_bbox_not_cell_halo`. The minimal retained input has an isolated singleton plus an L-shaped component; the canonical output paints `(2,5)` green while the rival leaves it black. Evidence: `repo/generators/7185b8225f1c/counterexamples/cell_halo_only.json` and `checks/counterexamples/7185b8225f1c-cell-halo/racket.json`.

**Alternatives rejected.** Identity, per-component outlines, and “paint only holes” are easier to refute and do not explain every canonical pair. A per-cell one-step halo is stronger because it is answer-equivalent on the complete labeled canonical population.

**Limit.** This is a finite plausible rival, not a proof that no other program fits the lessons.

## D2 — Alternate a guaranteed witness slot with a broad slot

**Decision.** `schedule_profile` uses `sample_index % 2`: even indices are `bbox_witness`, odd indices are `broad`. Witness slots select `polyomino_concave` or `polyomino_mixed` and restrict the concave shape to one that separates full bounding-box fill from the cell-halo rival. Construction retries if nuisance singletons accidentally erase the distinction. Broad slots use `PUBLIC_PROFILES * 16 + GENERAL_PROFILES * 3`.

**Why.** With three demonstrations drawn from any four consecutive pairs, a period-two witness schedule guarantees that every query rotation leaves at least one witness in the demonstrations. The weighted broad slot keeps exact public-family support above the frozen floor while retaining all thirteen scene profiles.

**Probes.** `test_every_scheduled_witness_slot_actually_refutes_cell_halo`, `test_every_consecutive_four_pair_window_survives_all_query_rotations`, and the 1,200-draw profile census in `test_default_schedule_retains_all_profiles_and_public_support` pass. The source-bound lesson census materialized 300 four-pair lessons and found zero ambiguities in production or any of 1,200 query rotations.

**Alternatives rejected.** A purely random witness frequency reproduced the prior shortcut. Scheduling by `(seed + sample_index) % 2` was rejected because common probes pair `seed = K + sample_index`, making the parity constant and destroying broad support. Declaring `LESSON_SCHEDULE_PERIOD=2` was unnecessary because the task-local test exhausts all cyclic starts; the shared checker would require a separately consumed fixed-seed enumeration receipt.

**Failure mode.** An explicit `scene_profile` override may request a non-witness profile. That is intentional: exact controls take precedence over the default curriculum, and `observe_overrides` verifies the requested profile.

## D3 — Fail closed on call scalars

**Decision.** Validate `seed` with `type(seed) is int`; validate `sample_index` the same way and require it to be nonnegative. Apply the same validation in `schedule_profile`.

**Why.** The pinned baseline accepted Booleans, floats, strings, `None`, and negative sample indices, producing 33 strict-scalar warnings across bands. The new focused tests first failed on all invalid probes and then passed after the minimal validation change.

**Alternative rejected.** `isinstance(value, int)` accepts Booleans. Coercing with `int(...)` silently changes caller intent.

## D4 — Declare an executable semantic contract

**Decision.** Add `EXAMPLES_NEEDED=3`, `MIN_STRICT_FRAC=1.0`, `strict_canonical_like`, the rival/witness registries, and `lesson_identifiable`. The hook validates every labeled pair, then reports ambiguity only when a declared rival fits all demonstrations and changes the query answer.

**Why.** The before semantic stage reported `NO_CONTRACT`. The after stage accepted all six canonical inputs, measured strict support 600/600, observed the witness 317/600, verified 60/60 bounded rival claims, passed 12/12 sampled lessons, and found 0/48 ambiguous smoke-test rotations.

**Limit.** The hook scores one declared rival identity. It does not establish universal induction.

## D5 — Preserve rule semantics; synchronize selected authority text

**Decision.** Do not alter the canonical Racket program or `RULE_HASH=df2d840acdd1`. Apply the explicit `authority-sync --selected-only` proposal to the training and augmented selected `target_code` fields. Preserve both archival `raw_code` fields.

**Why.** Baseline execution parity passed, but exact active authority text had two groups. The approved formatting-only tool changed only `/racket_target/target_code`; after-battery authority and rule-smoke stages are green.

**Changed file hashes.** Training base: `076274ed905f3a236c7f947e8832ab58084932b8a7cc4c751f12546911fcace5`; augmented base: `49df69c5b6d64cafd41adf883d51a2b073d6a640164bd4ac7b147a04e58f91cb`.

## D6 — Prototype only one reasoning-preserving rule parameter

**Decision.** Keep `halo_radius ∈ {1,2}` in `workspace/parametric/` and out of production. Select one radius per episode; use three demonstrations and one query; ensure every pair distinguishes the settings. Radius 1 emits the exact canonical source, while radius 2 changes only the four range bounds.

**Why.** Expansion distance is a small parameter that preserves object roles, connectivity, bounding-box reasoning, clipping, and paint semantics. Color changes, alternative connectivity, and singleton behavior would change semantic roles rather than parameterize the original reasoning pattern.

**Evidence.** Two episodes, eight pairs, sixteen Racket rule applications, sixteen Python-mirror matches, eight rotations, and eight alternate-setting refutations; zero survivors or ambiguities. Rule SHA-256 values are `6a061ebb...06c9` for radius 1 and `334c90dc...5934` for radius 2.

**Limits.** The prototype deliberately keeps the multi-cell component two cells from the border and places singleton contrasts outside the radius-two box. It is not a production-distribution proposal or approval claim.

## D7 — Do not modify the inherited frozen fixture

**Decision.** Leave `tests/test_generator_7185b8225f1c.py` unchanged, even though its fixed `parents[1]` lookup fails in the portable runtime. Add all new portable tests in separate files using `reviewer_support.find_root` and `load_selected_generator`.

**Why.** The assignment explicitly freezes the baseline fixture and assigns its migration to the library maintainer. Editing it would hide an inherited portability defect and violate return scope.

**Consequence.** Focused new tests pass 19/19 and 12/12, and the full generator battery is 12/12 green, but the explicit `task_tests` stage remains blocked at preflight. Completion is therefore reported as blocked rather than aggregate-pass.

## D8 — Final self-review for newly introduced shortcuts

The alternating schedule itself is not answer-bearing: `schedule_profile` changes only scene topology, while the same rule applies in both slots and across all explicit overrides. A learner could infer “concave examples occur at even sample indices” only from external index metadata, which public grids do not expose; it would not predict outputs without the bounding-box rule. The broad slot still covers every original profile, and the exact-override tests show no new restriction on the advertised `scene_profile` domain.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/7185b8225f1c/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
