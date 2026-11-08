# Current notes: ebd08d719ed6

Verification basis: repair accepted against the exact source and rule pins. Battery, census, audit and solve results below are reviewer-reported unless an owner rerun is explicitly named. `checks/...` and `solve/...` citations name the original transport paths; retained evidence is indexed in `evidence/review_index.json` and the task-local counterexample/solve directories.

## Intended rule and authority

Color-9 divider rows and columns partition the input into 3×3 tiles. Count the nonzero cells in each tile; exactly one tile has the largest count. Recolor only that tile's nonzero cells to color 8 and preserve every other cell. The unchanged canonical Racket authority is pinned by `RULE_HASH = "f5f6e2df9282"`.

## Prior state and repair

The prior audit `review-4ad4d70cba3eb50c:v0001` was open at the baseline and used as a lead; its contract/distribution findings are now explicitly resolved by the accepted v3.0.0 repair. Its source hash matched the selected baseline (`7b2d9d99fa474e43a0684b48e5987c1b78438d1069a27d5cd7b448a188165e46`), so its findings were rechecked against current bytes rather than treated as historical claims.

Version 2.1.0 advertised ten controls, but several were dead or singleton, difficulty clipped documented row/column domains, unknown overrides were accepted, and degenerate textures entered the ordinary public domain. It used a distinct color per tile and could not emit the canonical 7×7/three-color profile. Its `self_check` also accepted a one-tile lattice. The before battery retained in `checks/before/` failed lint, defect lint, and override, with profile-floor and semantic-gate advisories.

Version 3.0.0 replaces that surface with four exact, pixel-observable axes:

- `tile_rows`: 2..4
- `tile_cols`: 2..4
- `count_profile`: `canonical_2345`, `max4_no5`, or `max7_with5_distractor`
- `palette_profile`: `canonical_single` or `mixed_shared`

Every axis value is legal in every difficulty band, unknown or ill-typed overrides fail loudly, and `observe_overrides` recovers the exact requested values from pixels. Degenerate textures and inert palette aliases were removed from the public domain.

## Teaching schedule and shortcut coverage

`EXAMPLES_NEEDED = 3`. Consecutive default examples cycle through:

1. a canonical 2×2 lattice with occupancies {2,3,4,5} and foreground color 2;
2. a unique maximum of 4 with no five-cell tile;
3. a unique maximum of 7 with a five-cell distractor.

The strongest canonical-fitting rival is `fixed_five`: recolor the tile containing exactly five occupied cells. It matches all three canonical pairs. Profiles 2 and 3 are exact counterexamples, and the retained example at `counterexamples/fixed-five/` is bound to the final generator and canonical rule hashes. The focused tests cover all three cyclic starts and every query rotation over four consecutive examples.

## Validation and evidence

`self_check` now validates ARC colors, exact one-cell color-9 separators, 2..4 by 2..4 3×3 tiles, nonempty monochrome tile foregrounds from shared colors 2/3, a unique maximum, and one of the declared count/palette profiles. `strict_canonical_like` requires the exact canonical coarse profile: 2×2, occupancies {2,3,4,5}, and foreground color 2. `rule_mirror` is independent test support; Racket remains authoritative.

Final generator SHA-256: `11501342d0db51f960e1e805844fd2c6949936c3c8e7988fc563b86f44af2ae8`.

- Final battery: 12/12 stages green (`checks/after/checks/ebd08d719ed6_after_battery_summary.json`).
- Focused portable tests: 18/18 passed (`checks/task-tests-final/result.json`).
- Large lesson census: 300/300 lessons, 1,200/1,200 query rotations, zero declared-rival ambiguity or scoring errors (`checks/lesson-census.json`).
- Visible-only post-repair solve: 3/3 visible examples in one revision, with earlier exposure declared (`solve/summary.json`).

## Known limits and open findings

The generator deliberately teaches maxima 4, 5, and 7, not every possible occupancy maximum 1..9. It uses only shared foreground colors 2 and 3, each tile is monochrome, and the semantic checks cover the declared fixed-five rival rather than every imaginable hypothesis. The finite census supports the stated schedule and rotations but is not a proof of universal induction. No Racket rule change was made, and training approval remains outside this review.
## Current reviewer considerations

Source SHA-256: `11501342d0db51f960e1e805844fd2c6949936c3c8e7988fc563b86f44af2ae8`.

# Decisions for ebd08d719ed6

## D1 — Treat the unresolved audit as a lead, not proof

**Prior choice:** Version 2.1.0 exposed ten axes, four helpful palette aliases, and three degenerate textures. The rationale was not documented beyond a comment about widening lattice sizes and varying the densest count.

**Decision:** Reproduce current behavior first. The selected generator SHA matched unresolved return `review-4ad4d70cba3eb50c:v0001`, but the before battery and direct source inspection were used as the evidence of record.

**Probe:** `checks/before/checks/ebd08d719ed6_before_battery_summary.json` plus the TDD red run `checks/tdd-red.log`.

**Failure mode avoided:** Repairing stale symptoms or accepting a prior reviewer claim without confirming the selected bytes.

## D2 — Replace, rather than patch, the dishonest public axis surface

**Prior choice:** `tile_rows`, `tile_cols`, `palette_kind`, `max_density`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture` were declared, but difficulty clipped integer domains, palette aliases did nothing, several axes were singletons, and degenerate textures were callable as ordinary values.

**Alternatives considered:**

1. Keep all axes and make every one behaviorally meaningful. Rejected: most did not serve the task and would add unnecessary combinatorics.
2. Mark inert axes diagnostic. Rejected: callers need exact, useful controls rather than metadata-only knobs.
3. Keep only observable semantic controls. Selected.

**Decision:** Expose four axes: exact lattice rows/columns, a count profile, and a palette profile. All values are legal in all bands and recoverable from returned pixels.

**Probe:** Final override matrix in `checks/after/checks/ebd08d719ed6_after_override_results.json`; focused test `test_every_declared_override_is_exact_in_every_band`.

**Limitation:** The reduced surface intentionally omits arbitrary maxima and arbitrary color palettes.

## D3 — Anchor every three-example lesson to the canonical coarse profile

**Prior choice:** Random 2..4 by 3..6 lattices and per-tile colors made exact canonical-like draws effectively absent; profile floor measured 0/60.

**Alternatives considered:**

1. Weight random choices toward 2×2/color-2. Rejected: weighting cannot guarantee every short lesson contains an anchor.
2. Replay canonical grids. Rejected: this would reduce shape diversity and memorize examples.
3. Schedule a generated canonical-profile anchor every third sample. Selected.

**Decision:** Slot 0 is always a generated 2×2 lattice with counts `{2,3,4,5}` and foreground color 2. Shapes and target location remain seed-dependent.

**Probe:** Final profile floor green; semantic census strict rate 212/600, above declared floor 0.30.

**Failure mode:** A learner might overfit to the anchor alone; slots 1 and 2 therefore carry contrastive profiles.

## D4 — Name and execute the strongest canonical shortcut

**Observation:** Every canonical pair has tile occupancies `{2,3,4,5}`, so “recolor the five-cell tile” exactly matches all three labels.

**Alternatives considered:**

1. Only vary target position. Rejected: fixed-five ignores position.
2. Use a maximum of 4 with no count-5 tile. Useful but alone leaves behavior when a distractor count 5 exists untested.
3. Use both max-4/no-five and max-7/with-five-distractor. Selected.

**Decision:** Slots 1 and 2 implement those two profiles. `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, and `WITNESS_RIVALS` declare executable checks.

**Probe:** `counterexamples/fixed-five/`, 18 focused tests, semantic witness 388/600, and 300-lesson census with zero production or rotation ambiguity.

**Limitation:** This refutes fixed-five, not every possible profile-specific hypothesis.

## D5 — Use shared colors instead of one color per tile

**Prior choice:** Tile index selected colors 1..7, making palette size grow with lattice size and allowing target identity to correlate with per-tile color.

**Alternatives considered:**

1. Canonical color 2 only. Rejected as the sole profile because it would not show color irrelevance.
2. Arbitrary independent colors per tile. Rejected because it recreates palette drift and uniqueness shortcuts.
3. One shared color or two reused shared colors. Selected.

**Decision:** `canonical_single` uses color 2 everywhere; `mixed_shared` reuses colors 2 and 3 across multiple tiles. Each tile remains monochrome.

**Probe:** Defect lint and distribution gate green; exact palette observation in focused tests.

**Limitation:** The generator does not test multicolor occupancy within a tile or colors outside 2/3.

## D6 — Validate the declared domain, not merely the unique maximum

**Prior choice:** `self_check` mostly found full 9-lines, accepted a single tile, did not constrain colors, and did not ensure a declared teaching profile.

**Decision:** Parse exact 3×3 tile geometry and one-cell separators; reject malformed ARC colors, stray/missing separators, lattices outside 2..4, empty or multicolor tiles, unsupported foreground colors, ties, and undeclared count signatures. `strict_canonical_like` separately identifies the narrow canonical manifold.

**Probe:** Focused mutation/degenerate tests and final self-check/grammar/defect-lint stages.

**Failure mode:** This is intentionally stricter than the mathematical rule's universal domain. It describes generated training support, not every grid the Racket program could transform.

## D7 — Preserve the canonical authority

**Decision:** Do not modify the Racket rule. Add the canonical `RULE_HASH = "f5f6e2df9282"`, an independent Python `rule_mirror` for tests, and supported-Racket evidence for the retained counterexample.

**Probe:** Rule smoke, Racket lint, and authority sync all green; `counterexamples/fixed-five/racket.json` records executed/catalog rule-hash equality.

**Failure mode avoided:** Silently changing the task to fit the generator.

## D8 — Test complete lessons and rotations, not only witness frequency

**Decision:** Add a focused test covering all three cyclic starts and every possible held-out query among four consecutive examples. Run the source-bound larger census with 100 lessons per band and `--rotate-query`.

**Probe:** `test_every_cyclic_lesson_start_and_query_rotation_refutes_fixed_five`; `checks/lesson-census.json` reports 300/300 production lessons and 1,200/1,200 rotations with zero ambiguity.

**Limitation:** The census is finite and checks declared rivals. It does not prove unique induction against undeclared rules.
