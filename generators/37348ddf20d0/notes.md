# Working notes: 37348ddf20d0

## 2026-09-28 review-f908585c1db6f10d

- Canonical rule hash pinned to `6d8410c29906`; no Racket semantic change was justified.
- Replaced the random border/stub sampler with five recoverable semantic profiles.
- Any five consecutive sample indices cover all profiles exactly once.
- Public exact axes are now only `grid_h`, `grid_w`, `n_red`, `n_green`, and `texture`; the full Cartesian domain is valid in every band.
- Added pure Python BFS mirror, four witnesses, three named rival solvers, and `lesson_identifiable()`.
- Added task-local regression tests with an independent BFS implementation.
- Required after battery: 12/12 green; semantic gate 600/600 strict and 12/12 lessons; override gate 14,850 accepted draws with no findings.

## Future checks

- If episode assembly stops using consecutive sample indices, rerun `lesson_identifiable()` on the final assembled episode.
- When adding a new texture, require exact `observe_overrides()` recovery and at least one named rival it falsifies.
- When changing the rule source/hash, replay every canonical pair and the Racket/Python parity census before carrying this curriculum forward.
- Expand the rival set only with a canonical-validated counterexample; do not add speculative rivals that could create false-positive lesson rejection.
## Current reviewer considerations

Source SHA-256: `222bb3faed0e93a1ef53073874042a3e63e7e150fff1b49564f0735996448ba6`.

# Design decisions: 37348ddf20d0

## D1. Preserve the canonical Racket rule

**Original rationale:** The imported generator described wall-aware nearest-seed filling, but its docstring ambiguously said ties were “left blank or marked.” No retained design evidence explained that wording.

**Decision:** Pin rule hash `6d8410c29906` and leave the Racket source unchanged. Canonical examples and direct execution show that finite ties and equally unreachable cells remain black.

**Alternatives considered:** Rewrite the Racket for style; change tie behavior; make the Python mirror authoritative.

**Probes:** All five canonical pairs; 120 generated Racket applications; A-B-A reentrancy; input mutation checks; 120/120 Python-mirror parity; authority-sync gate.

**Failure modes guarded:** Accidental rule drift, tie recoloring, state leakage, hidden source divergence.

**Limitation:** Style advisories remain in the canonical program. They are not correctness defects.

## D2. Constrain ordinary dimensions to the canonical envelope

**Original rationale:** The old declaration advertised `grid_h=5..24` and `grid_w=7..24`, while difficulty branches accepted much narrower ranges. The broad values had no documented canonical justification.

**Decision:** Use exact dimensions 11..13, with the five default profiles scheduled on `(12,11)`, `(11,12)`, `(13,11)`, `(11,13)`, and `(12,12)`—the five canonical input shapes.

**Alternatives considered:** Preserve broad 5..24 ranges; use one fixed shape; retain band-specific bounds.

**Probes:** Canonical profile floor, full boundary override matrix, all canonical pairs, diversity census.

**Failure modes guarded:** Shape-distribution drift, declared-but-rejected overrides, zero canonical support in a band.

**Limitation:** The generator does not stress grids larger than 13×13.

## D3. Expose only exact, recoverable axes

**Original rationale:** The old nine-axis surface appeared intended to offer broad control, but `palette_kind`, `anchor_row`, `seed_distance`, singleton palette axes, and helpful textures were disconnected or unobservable.

**Decision:** Expose only `grid_h`, `grid_w`, `n_red`, `n_green`, and `texture`. Every value is consumed through keyed GenCtx draws and recovered by `observe_overrides()`.

**Alternatives considered:** Keep dead controls as diagnostic metadata; add many internal layout choices as public axes; declare a large incompatibility table.

**Probes:** 14,850 official override-contract draws; 2,160 manual full-Cartesian draws; unknown-key and invalid-band tests.

**Failure modes guarded:** Silent typo acceptance, axis drift, provenance gaps, difficulty-dependent rejection, untestable metadata.

**Limitation:** Divider positions and seed placement details vary internally and cannot be directly overridden.

## D4. Replace random wall stubs with five rule-bearing profiles

**Original rationale:** Version 2.0.0 explicitly tried to improve diversity over a trivial one-red/one-green split by adding multiple seeds and short wall stubs. That improved surface diversity but did not guarantee semantic coverage.

**Decision:** Construct five named topologies: open Voronoi, decisive wall detour, finite tie rooms, seedless rooms, and mixed complete partitions.

**Alternatives considered:** More random maze generation; only reproduce canonical complete partitions; post-filter random grids until witnesses happen.

**Probes:** Four witness predicates over 600 official draws; named rival disagreements; canonical strictness; lesson identifiability.

**Failure modes guarded:** Manhattan-distance shortcut, tie-breaking shortcut, first-seed-only shortcut, treating isolated chambers as fillable.

**Limitations:** Hand-built profiles sample a structured topology family rather than the full space of mazes.

## D5. Use a five-demonstration cyclic lesson schedule

**Original rationale:** The old generator sampled each grid independently; no rationale linked examples into an identifiable lesson.

**Decision:** `schedule_profile(seed, sample_index)` cycles all five profiles in any consecutive window of five. Set `EXAMPLES_NEEDED = 5`.

**Alternatives considered:** Independent random profile choice; weighted random choice; fixed profile by difficulty.

**Probes:** 3,000 sliding windows; official 12-lesson semantic gate; task-local lesson tests.

**Failure modes guarded:** A named wrong rule fitting all demonstrations and changing the query; random lessons missing rare semantics.

**Limitations:** The deterministic cycle can be inferred from sample metadata. Downstream nonconsecutive assembly must rerun the lesson gate.

## D6. Vary exact seed counts by difficulty while preserving all profiles

**Original rationale:** Version 2.0.0 increased seed counts to avoid a trivial left/right split; that motivation was sound.

**Decision:** Keep exact count axes at 1..4 and schedule defaults from two seeds per color on easy through up to four per color on hard. Every topology still accepts the full 1..4 Cartesian domain.

**Alternatives considered:** Always one seed per color; counts tied strictly to texture; unrestricted random counts.

**Probes:** Multiple-seed witness, first-seed rival, override matrix, input/output diversity.

**Failure modes guarded:** First-red/first-green shortcut, collapsed easy outputs, count overrides that cannot be placed.

**Limitation:** The easiest defaults still contain at least two seeds for most profiles to keep the semantic branch observable.

## D7. Remove negative fixtures from the ordinary texture domain

**Original rationale:** The old texture enum mixed `no_seeds`, `no_walls`, and `seeds_collide` with helpful modes, apparently as diagnostics. `seeds_collide` was actually lawful, while the others violated the ordinary grammar.

**Decision:** Ordinary `texture` contains only five lawful, productive profiles. Malformed cases are covered by tests instead of being advertised as training modes.

**Alternatives considered:** Maintain a separate diagnostic API; mark a lawful degenerate list; keep them and weaken `self_check`.

**Probes:** defect lint, override contract, destructive mutation tests.

**Failure modes guarded:** Invalid grids entering training, texture-domain overlap, metadata-dependent self-check bypass.

**Limitation:** There is no public generator mode for intentionally malformed negatives.

## D8. Add a pure Python rule mirror and named rivals

**Original rationale:** No semantic contract existed, so the prior generator could pass morphology/diversity checks without proving it taught the transformation.

**Decision:** Add independent multi-source BFS, semantic witnesses, and explicit wrong-rule implementations. Use them in tests and `lesson_identifiable()`.

**Alternatives considered:** Compare only against Racket; use natural-language witness descriptions; rely on random output diversity.

**Probes:** canonical parity, 120 Racket parity draws, witness/rival census, targeted reproducer tests.

**Failure modes guarded:** Correct-looking grids with wrong outputs, witnesses that do not actually refute the claimed rival, semantically ambiguous lessons.

**Limitations:** Rival coverage is curated, not exhaustive.

## D9. Keep `self_check` canonical-compatible and enforce topology separately

**Original rationale:** The old checker validated border/seeds/open cells but did not connect advertised textures or overrides to observable structure. At the same time, two authoritative canonical inputs use full-column partitions that do not fit the generator's five exact topology signatures, so making topology recognition a universal admission rule would reject valid task data.

**Decision:** Keep `self_check()` as a strict task-grammar check for palette, dimensions, border, seed counts, and open cells. Enforce exact generated topology and public-axis recovery in `generate()` through `observe_overrides()`, and enforce semantic content through witnesses, rivals, lesson checks, and regression tests.

**Alternatives considered:** Make every input match a generator profile; add metadata-dependent exceptions inside `self_check`; leave override recovery to the official battery only.

**Probes:** 60 default official instances, all five canonical inputs, 45 destructive official mutations, the full override matrix, direct `observe_overrides()` assertions, and task-local targeted mutations.

**Failure modes guarded:** Ragged grids, invalid colors, broken borders, missing seed colors, generated-profile drift, and metadata-dependent admission of malformed instances.

**Limitation:** `self_check()` alone proves task grammar, not a named generated topology or semantic identifiability; the constructor/observer and witness layers cover those stronger claims.

## D10. Add task-local regression tests as a future-agent tool

**Original rationale:** No task-local tests were present.

**Decision:** Add a focused test module with an independent solver, exact boundary matrix, semantic rival reproducers, replay/purity checks, diversity floors, and mutation rejection.

**Alternatives considered:** Depend only on the repository battery; add an ad hoc one-off script.

**Probes:** Watched the new tests fail against the old code, then pass after implementation; final result 15/15.

**Failure modes guarded:** Regression in canonical semantics, public axis contract, schedule coverage, determinism, purity, or lesson identifiability.

**Limitation:** The runtime workspace command does not automatically copy newly added task-local test files, so the focused suite currently requires copying the test into a staged runtime or running after integration.
