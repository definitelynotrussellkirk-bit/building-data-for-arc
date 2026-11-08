# Working notes: c05faa9b2b85

## Baseline observations

Baseline generator SHA-256 was `c27f4470b1f94f90b77d10d74b3b735ad4fc6af9d3e0da395b372db85566aad0` (version 1.2.1). The retained associated-notes file was empty, so there was no task-specific prior return to adopt; `b90d4c3d5553` was consulted only as a passing contract/layout precedent.

The interrupted before battery retained decisive failures:

- missing required `RULE_HASH` plus five collapsed/unprobed axes (`checks/before/checks/c05faa9b2b85_before_lint.log`);
- one identity case in 120 Racket applications (`checks/before/checks/c05faa9b2b85_before_rule_smoke.log`);
- a weak validator that rejected only 16/55 destructive mutations and checked presence rather than chamber semantics (`checks/before/checks/c05faa9b2b85_before_selfcheck.log`).

Manual semantic review found that all generated chambers were disjoint rectangles. Thus the plausible rival “fill only rectangular frame interiors” fit all five canonical pairs and the entire old distribution. Rejection sampling also allowed identity cases.

## Repair decisions

The implementation was replaced with a deterministic, rejection-free constructor and pinned to canonical rule hash `080731f15c8c`. Three exact, observable axes remain:

- `scene_profile`: `canonical_rectangles`, `single_notch`, `double_notch`;
- `canvas_profile`: 10×14, 11×15, or 12×16;
- `n_rooms`: 2, 3, or 4.

The default scene schedule is period three. Every three consecutive demonstrations therefore include all scene profiles. Semantic profiles contain:

1. irregular active chambers, refuting `rectangular_regions_only`;
2. one chamber with two different marker colors, refuting `first_color_wins`;
3. one chamber with two cells of the same marker color, refuting `exactly_one_marker_cell`.

The third case was added after a final adversarial self-review caught that the v2.0.0 draft still taught marker-cell count rather than distinct-color count. Its failing-then-passing regression is retained in `checks/tdd/red-repeated-seed.log` and `checks/tdd/green-repeated-seed.log`.

Difficulty is observable through the default canvas: easy 10×14, medium 11×15, hard 12×16. An intermediate battery found byte-identical difficulty bands; the failing result is retained under `checks/after/`, and the corrected final battery is under `checks/after-final-v2/`.

`self_check` now validates the full generated grammar, exact override realization, connected exterior, enclosed chamber count, marker cardinality, color ownership, nonidentity support, and the allowed mixed/repeated-marker cases. `strict_canonical_like` separately recognizes the published rectangular one-marker support.

## Final evidence

Final generator SHA-256: `45f9a28efbeb04b199056b93d4db1ffd66e13b64384ae8449657d217dd650b27`.

- focused task tests: 41/41 (`checks/task-tests-final-v3/result.json`);
- full battery: 12/12 green (`checks/after-final-v2/checks/c05faa9b2b85_after_battery_summary.json`);
- exact semantic probe: 3/3 canonical shortcuts fit all 5 canonical pairs, all 27 override combinations construct/observe/nonidentity, all 3 cyclic lesson starts identify the rule (`checks/semantic-probe-v2.json`);
- production census: 300/300 lessons, 1,200 query rotations, 1,200 unique inputs, zero declared-rival ambiguities (`checks/lesson-census-final-v2.json`);
- exact supported Racket witness agrees with the Python mirror and disagrees with all three rivals (`checks/shortcut-witness-v2/witness.json`).

No Racket authority or canonical row was changed.

## Known limits

This is finite evidence against three declared plausible rivals, not a proof of unique induction against every possible rule. The generated grammar deliberately keeps color 1 as the wall, uses a small fixed slot family, emits no enclosed seedless chamber, and keeps each marker color within one chamber. These restrictions are explicit rather than advertised as broader coverage.
## Current reviewer considerations

Source SHA-256: `45f9a28efbeb04b199056b93d4db1ffd66e13b64384ae8449657d217dd650b27`.

# Decisions for c05faa9b2b85

Final generator SHA-256: `45f9a28efbeb04b199056b93d4db1ffd66e13b64384ae8449657d217dd650b27`.

## D1 — Preserve the canonical authority

**Choice.** Pin `RULE_HASH = "080731f15c8c"` and change only the generator-side distribution and contracts.

**Rationale.** The canonical outputs and Python mirror agreed on all five usable canonical pairs; the defect was teaching coverage, not the rule.

**Alternatives rejected.** Editing the Racket rule or canonical row would have changed a correct authority to solve a generator problem.

**Probe/failure mode.** Authority-sync, Racket-lint, canonical mirror tests, and the supported exact witness all bind to the unchanged hash. A future canonical change must intentionally update the pin and rerun these checks.

## D2 — Use a rejection-free constructor

**Choice.** Paint fixed room boxes as walls and carve exact connected interiors.

**Rationale.** The old random placement/rejection path generated an identity case and made support hard to reason about. Exact construction guarantees 2–4 enclosed chambers, fillable cells, enough marker positions, and deterministic observability.

**Alternative rejected.** Keep rejection sampling and add more retries. This would reduce but not remove silent support holes and identity risk.

**Limit.** Geometry uses four predefined slots per canvas; it is deliberately not broad free-form topology.

## D3 — Three scene profiles

**Choice.** `canonical_rectangles`, `single_notch`, and `double_notch`.

**Rationale.** One canonical profile preserves direct support. Both semantic profiles make connected regions visibly nonrectangular while remaining simple enough to infer.

**Alternative rejected.** Arbitrary mazes or concave polygons would broaden shape support but add irrelevant search complexity and make exact override recognition fragile.

**Probe.** `observe_overrides` recovers the profile by component rectangularity and bounding-box deficit; all 27 joint override combinations are exact in `checks/semantic-probe-v2.json`.

## D4 — Teach distinct-color cardinality, not marker-cell count

**Choice.** Every semantic profile contains two distinct special chambers: one with two different colors (unchanged) and one with two cells of the same color (filled).

**Rationale.** The rule depends on the number of **distinct colors**. A mixed chamber alone refutes `first_color_wins` but does not refute `exactly_one_marker_cell`.

**Rejected initial design.** v2.0.0 used only a mixed two-color chamber and globally one-cell colors. A failing test proved the marker-count rival survived (`checks/tdd/red-repeated-seed.log`).

**Failure mode controlled.** A marker color may repeat within one chamber but may not occur in multiple chambers. The grammar allows at most one repeated-same-color chamber and one mixed chamber.

## D5 — Period-three teaching schedule

**Choice.** `sample_index % 3` selects the scene profile; `EXAMPLES_NEEDED = 3`.

**Rationale.** Every three consecutive demonstrations contain one canonical and two semantic scenes, so all three declared rivals are refuted regardless of cyclic start.

**Alternative rejected.** Independent random profile selection could produce all-canonical lessons or omit a required witness.

**Probe.** The reusable semantic probe enumerates starts 0, 1, and 2; the production census covers starts 0–99 per band and every query rotation.

**Limit.** This guarantee assumes downstream assembly uses consecutive samples as declared; other assembly policies must recheck identifiability.

## D6 — Observable difficulty through canvas size

**Choice.** Easy defaults to 10×14, medium to 11×15, and hard to 12×16. Explicit canvas overrides remain legal at every band.

**Rationale.** The first repair left difficulty unused; `defect_lint` correctly reported byte-identical bands.

**Alternative rejected.** Difficulty-dependent room count would entangle two axes and reduce joint support. Canvas size changes cost while preserving the semantic rule.

**Probe.** Nine sample indices are tested across all bands; final `defect_lint` and override stages pass.

## D7 — Room count 2–4

**Choice.** Keep an exact `n_rooms` axis over 2, 3, and 4.

**Rationale.** Two rooms are sufficient to host the mixed and repeated-same-color witnesses; higher counts add ordinary positive chambers without changing the law.

**Alternative rejected.** One room cannot simultaneously teach both decisive marker cases. More than four exceeds the simple palette/slot budget without adding semantic value.

## D8 — Palette and marker ownership

**Choice.** Draw colors 2–9 without reuse across chambers; permit one selected color to occupy two cells within its chamber.

**Rationale.** This isolates the intended same-color multiplicity test while avoiding a separate ambiguity about whether equal colors link disconnected chambers.

**Alternative rejected.** Reusing a color across rooms would test another law not needed to repair the canonical shortcut and could encourage global-color grouping.

**Limit.** Cross-chamber color reuse is untested and outside the documented generated grammar.

## D9 — Full grammar validation plus a canonical profile

**Choice.** `self_check` validates ARC shape/types, a seedless exterior, 2–4 enclosed components, marker counts, color ownership, at most one mixed room, at most one repeated room, and at least one active region. `strict_canonical_like` additionally requires rectangular chambers with one marker cell each.

**Rationale.** Generator validity and canonical likeness are different questions. The baseline presence-only check accepted many destructive mutations.

**Alternative rejected.** Encoding only generation-time assertions would leave external inputs and portable checks under-specified.

**Probe.** Final selfcheck, grammar, profile-floor, and task-test stages all pass.

## D10 — Executable rivals and witnesses

**Choice.** Declare three pure rivals—`rectangular_regions_only`, `first_color_wins`, and `exactly_one_marker_cell`—under all required rival registries, plus one witness predicate per rival.

**Rationale.** Canonical compatibility is itself measured, then complete lessons must refute every rival. The workspace probe iterates the declarations rather than a copied list.

**Alternative rejected.** A prose-only argument is easy to stale when the distribution changes.

**Limit.** These are the strongest identified plausible shortcuts, not an exhaustive hypothesis class.

## D11 — Tests and retained failures

**Choice.** Use TDD for authority binding, 27 override combinations, semantic witnesses, canonical shortcut fit, cyclic lessons, determinism/diversity, invalid overrides, and difficulty separation.

**Rationale.** The red logs demonstrate that tests detect the missing behavior rather than merely describing the implementation afterward.

**Retained failures.** Initial 39-test red, dead-band red, marker-count red, interrupted before battery, and failed intermediate battery remain under `checks/`.

## D12 — No shared-code patch

**Choice.** Keep all production changes within the selected task; put general tool suggestions only in `FEEDBACK_TO_CODEX.md`.

**Rationale.** The return contract forbids unrelated shared edits, and no shared change was needed to complete the repair.
