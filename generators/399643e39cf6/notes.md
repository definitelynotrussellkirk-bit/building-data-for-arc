# Current notes: `399643e39cf6`

## Intended rule

Sort the two color-9 markers in row-major order. Their displacement is the translation vector. Remove both markers, split the remaining nonzero cells into same-color 4-connected components, select the minimum by `(cell count, bbox top, bbox left, color)`, and paint one translated copy of that component while preserving every ordinary source component.

Canonical Racket rule hash: `00eb76bc4fb4`. This review did not change rule behavior. It only synchronized the selected bank entry's `target_code` text with its already-canonical `raw_code`, removing comment-only authority drift.

## Reversed baseline decisions

The pinned v2.0.1 source used randomly ordered markers, random object placement, permissive validation, degenerate textures, and several advertised controls that were ignored or incompatible with the sampler. Prior return `review-15543a49112076fa:v0001` supplied the marker-ordering lead; `review-3c2d78c5fc590735:v0001` supplied the topmost-shortcut lead. Both were reproduced against the pinned SHA `692f75e31221f8b51f2fa396184322a186ba937419aeb2ed332956fea4575df0` before repair.

The current v3.0.0 generator instead has seven strict observable axes: `grid_h`, `grid_w`, `vector_kind`, `selection_kind`, `small_shape`, `large_shape`, and `palette_kind`. Unknown, mistyped, and out-of-domain overrides are rejected. All 1,152 endpoint combinations tested are constructive and recover exactly through `observe_overrides`.

## Distribution and teaching policy

- Canvas: 8–10 rows by 9–11 columns, with an exact 8×9 canonical-profile slot in every difficulty band.
- Marker vectors: `(5,3)`, `(0,4)`, `(4,-3)`, and `(4,0)`. Every pair is row-major in the same order used by the authority.
- Selected shapes have 2–4 cells; larger distractors have 5–7. Tie scenes add an equal-size alternate so bbox ordering is observable.
- The selected color is not the minimum palette color, and the larger distractor is topmost, so every production draw refutes the canonical `lowest color` and `topmost` shortcuts.
- Every ordinary component's translated footprint is in bounds and initially empty, preventing clipping or overwrite from obscuring selector semantics.
- A deterministic four-slot schedule supplies all four vectors, unique and tie selection, a canonical profile, and visible rival witnesses. Lessons use three demonstrations and one query.

## Evidence and limits

Final generator SHA-256: `aa430fdc38ba0aa31ddde142ede83c234679faddc8e7c612e1a0473d404090e5`.

The final native battery is 12/12 green and the focused suite is 42/42 green. A 300-lesson census (100 per band) found zero ambiguity among 300 ordered lessons and 1,200 held-out query rotations against the declared rivals; fixed-seed schedule enumeration covered all four starts in all three bands with 12/12 lessons and 48/48 rotations identifiable. These finite checks do not prove uniqueness against undeclared hypotheses or all random seeds.

The exact canonical topmost-shortcut counterexample is retained under `counterexamples/review-eb6a2ce8eead7ff4/`. No open blocker remains for this repair; catalog approval remains a maintainer decision.
## Current reviewer considerations

Source SHA-256: `aa430fdc38ba0aa31ddde142ede83c234679faddc8e7c612e1a0473d404090e5`.

# Decisions for `399643e39cf6`

Assignment: `review-eb6a2ce8eead7ff4`
Pinned baseline generator SHA-256: `692f75e31221f8b51f2fa396184322a186ba937419aeb2ed332956fea4575df0`
Final generator SHA-256: `aa430fdc38ba0aa31ddde142ede83c234679faddc8e7c612e1a0473d404090e5`
Canonical rule hash: `00eb76bc4fb4`

## D1 — Treat row-major marker order as part of the input law

**Prior choice.** The baseline drew one marker and an arbitrary signed delta, checked translation bounds using that draw order, then painted two indistinguishable color-9 cells. The Racket authority obtains markers in row-major order. When draw order and row-major order disagreed, the effective vector reversed.

**Decision.** Every advertised vector is represented by a pair with `p1 < p2` in row-major order. Candidate construction derives and validates translation using that same ordered pair.

**Evidence.** Prior return `review-15543a49112076fa:v0001` identified ordinary easy seed 1/index 1: baseline validation reasoned about `(-3,0)`, while Racket used `(3,0)` and clipped one cell. The current regression replays that coordinate and checks the full generated-domain contract. The independent oracle and Racket parity test cover all three canonical inputs plus 32 generated inputs.

**Alternative rejected.** Preserve signed vectors and store marker identity outside the grid. The two marker cells have the same color, so identity would be invisible and the rule would still sort them geometrically.

## D2 — Construct layouts exhaustively, then sample a cached lawful candidate

**Decision.** For each exact axis tuple, enumerate placements of the selected shape, larger distractor, optional equal-size alternate, their translated footprints, and marker pair. Reject any layout with source/target overlap, clipping, overwrite, or marker collision. Cache only immutable geometry and use keyed RNG to choose among up to 256 candidates.

**Why.** Rejection sampling made rare boundary combinations fragile and made failures seed-dependent. Exhaustive construction makes every advertised combination either provably available or an immediate authoring error.

**Rejected first attempt.** Initial elongated six- and seven-cell shapes left no constructive layout for strict `8×9 + canonical vector + tie + tetromino` cases. The first green attempt therefore had 2/42 failures. Compact connected stair-step shapes replaced them; no compatibility exemption was added. Evidence: `checks/task-tests-green-1/result.json` followed by the final task-test report.

## D3 — Make exact controls observable and reject everything else

**Decision.** Retire the baseline pseudo-controls (`anchor_corner`, `asymmetry_force`, `palette_size`, `position_bias`, `n_distinct_colors`, `texture`) and expose only seven pixel-recoverable axes:

- `grid_h`: 8, 9, or 10;
- `grid_w`: 9, 10, or 11;
- `vector_kind`: canonical, horizontal, down-left, vertical;
- `selection_kind`: unique or tie;
- `small_shape`: domino, triomino, tetromino;
- `large_shape`: pentomino, hexomino, heptomino;
- `palette_kind`: canonical, warm, cool, broad.

`observe_overrides` reconstructs all seven values from the returned grid. Unknown names, `bool`-as-`int`, wrong types, unknown difficulty strings, and out-of-domain values are errors. `INCOMPATIBLE_OVERRIDE_COMBINATIONS` is empty because the full 1,152-case endpoint product is constructive.

**Alternative rejected.** Keep old names as aliases. Several had no coherent pixel-level meaning, and silent aliases would preserve the exact no-op behavior the override gate is intended to detect.

## D4 — Separate selector teaching from accidental clipping and overwrite

**Decision.** Require the translated footprint of every ordinary component—not only the selected one—to remain in bounds and initially empty. This makes the outputs of `largest` and `copy all` rivals well-defined and visibly wrong rather than accidentally hidden by clipping or overwrite.

**Why.** A lesson about choosing the smallest object should not rely on undefined edge behavior to refute a different selector. The stronger production invariant is checked independently by `workspace/reference_probe.py` and on 384 deterministic generated draws across `None`, easy, medium, and hard.

**Domain limit.** The Racket authority itself can clip writes on arbitrary inputs; the production generator intentionally does not teach that behavior. This is documented rather than generalized into a claim about the full authority domain.

## D5 — Refute the two canonical shortcuts in every production draw

**Observation.** All 3/3 canonical demonstrations are consistent with both “copy the topmost object” and “copy the lowest-color object.” These are declared in `CANONICAL_SHORTCUTS` and verified to fit rather than assumed.

**Decision.** Place a larger distractor before the selected object and assign the selected object a color larger than both competitors. Thus the true smallest object is neither topmost nor lowest-color. Tie scenes additionally put an equal-size alternate after the selected object so bbox tie-breaking is visible.

**Exact witness.** Easy seed 0/index 0 is retained at `generators/399643e39cf6/counterexamples/review-eb6a2ce8eead7ff4/topmost_shortcut.json`; actual Racket output is in `checks/repair/399643e39cf6/topmost_racket.json`.

**Alternative rejected.** Rely on random placement/palette to produce occasional counterexamples. A finite lesson could then contain no such witness even when the global distribution sometimes emits one.

## D6 — Use a four-slot rotation-safe teaching schedule

**Decision.** `EXAMPLES_NEEDED = 3` and `LESSON_SCHEDULE_PERIOD = 4`. Consecutive slots expose all four marker vectors, alternate unique/tie selection, cycle shapes and palettes, and reserve slot 0 for an exact canonical profile in every difficulty band. For each of the four possible starts, any one of the four pairs may be the query and the remaining three demos refute every declared competitor.

**Measured support.** The required semantic smoke run materialized 12 lessons (four per band) and found 12/12 identifiable plus 0/48 ambiguous query rotations. The larger random census materialized 300 lessons (100 per band), 1,200 rotations, and 939 unique inputs with zero ambiguity or scoring errors. Fixed-seed enumeration covered all four declared starts in all three bands: 12/12 lessons and 48/48 rotations.

**Limits.** The rival set is finite: topmost, lowest-color, largest, all-objects, reverse tie-break, keep markers, reverse vector, and fixed canonical vector. Passing does not establish uniqueness against every program or every random seed.

## D7 — Preserve canonical support without conflating it with all variation

**Decision.** Every band receives an exact `8×9`, canonical-palette slot. Other slots vary dimensions, vectors, shapes, palettes, and selection ties. `self_check` describes the complete lawful sampler manifold; the native profile-floor gate separately verifies canonical-profile support.

**Why.** Restricting every draw to the canonical profile would leave vector and selector shortcuts intact. Conversely, unconstrained variation can lose canonical support. A deterministic anchor gives both.

## D8 — Keep the canonical rule, normalize only selected-source text

**Decision.** Do not change the canonical Racket program or its behavior. The task-specific selected bank entry had `raw_code` and `target_code` differing only by explanatory comments. Set `target_code` byte-for-byte equal to `raw_code` so authority synchronization is exact.

**Evidence.** Canonical rule hash remains `00eb76bc4fb4`; final rule smoke, Racket lint, authority-sync, and execution parity pass. This is a source-text synchronization, not a semantic reference-rule change.

## D9 — Retain failures and use independent probes

**Decision.** Keep the interrupted before battery, 26-failure RED suite, two-failure constructive-shape iteration, and all later green receipts. Add `workspace/reference_probe.py` as a portable independent component/selection/vector oracle rather than testing only generator-internal helpers.

**Why.** The failures show which behavior each repair actually changed. The independent oracle reduces the chance that a generator bug and its test helper agree on the same mistake.

## Final measured scope

- Native after battery: 12/12 stages green.
- Focused portable tests: 42/42 green.
- Exact override product: 1,152/1,152 constructive and observable.
- Required semantic smoke: 600/600 strict draws; 12/12 lessons; 48/48 rotations.
- Random lesson census: 300/300 lessons and 1,200/1,200 rotations with no declared-rival ambiguity; 939 unique inputs.
- Fixed-seed declared-period census: 12/12 lessons and 48/48 rotations.
- Exposed solve: revision 1 matched 3/3 visible examples; earlier rule exposure recorded `yes`, reference consultation `no`.

These are source-bound finite measurements. Catalog/training approval remains outside this review.
