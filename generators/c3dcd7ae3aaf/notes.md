# Working notes: c3dcd7ae3aaf

## Review 2026-09-28

The imported `1.1.2` generator sampled only positive straight-triomino targets. Consequently, the wrong rule “recolor every cyan cell” matched every ordinary generated pair. Its checker also rejected all five canonical inputs because it treated lawful dominoes, L-triominoes, and size-four components as malformed.

Version `2.0.0` replaces retry-only target placement with a deterministic backtracking component planner. Ordinary draws always include:

- at least two targets;
- horizontal and vertical targets;
- one edge target and one interior target;
- an unchanged cyan L-triomino;
- an unchanged straight cyan domino;
- an optional varied size-four distractor.

Only observable axes remain: `grid_h`, `grid_w`, `n_targets`, and `n_distractors`. All declared values are legal in every difficulty band and round-trip through `observe_overrides`.

The canonical Racket authority was not changed. `RULE_HASH = 672defea5335` pins the selected rule, and the Python mirror is diagnostic/test-only.

Verification evidence is in the packet-level `checks/` directory. The final after battery is 12/12 green; focused tests are 18/18 green; the repository suite is 104 passed, 28 skipped when run with `PYTHONPATH=src` (the skipped tests require an external Racket executable, while the packet battery used its bundled Racket runtime).
## Current reviewer considerations

Source SHA-256: `b6bb6407ee263bdca8c57fb5ca5f3e22dcd6d5159569b181d1cb55f9560e7a9b`.

# Design decisions: c3dcd7ae3aaf

## 1. Keep the canonical Racket rule unchanged

**Original rationale:** Unknown from the imported notes. The selected rule already matched the written solution.
**Alternatives considered:** Rewrite the rule; change connectivity; add special handling for distractors.
**Probe:** Canonical pair execution, rule smoke, grammar gate, Racket lint, and authority sync.
**Decision:** Retain the rule and pin it with `RULE_HASH = 672defea5335`.
**Failure mode avoided:** A generator defect being “fixed” by weakening or changing the task authority.
**Limitation:** The Python mirror is not authority and must remain diagnostic only.

## 2. Use canonical dimensions 8..10

**Original rationale:** Imported defaults ranged 8..13, with hard examples 11..13; no rationale was recorded.
**Alternatives considered:** Preserve 8..13; use only the three exact canonical square sizes; allow 4..20 as declared previously.
**Probe:** Canonical profiles are `(8,8,2 colors)`, `(9,9,2)`, and `(10,10,2)`. The final profile census measured 25/60 exact and 60/60 in-envelope.
**Decision:** Expose independent `grid_h` and `grid_w` in 8..10. This preserves exact canonical support while allowing rectangular combinations.
**Failure mode avoided:** A hard band with zero canonical-scale support.
**Limitation:** The generator does not teach scale extrapolation beyond 10x10.

## 3. Make target count 2..4

**Original rationale:** Imported generator used 2..5 but exposed 1..10, with difficulty-specific incompatible ranges.
**Alternatives considered:** Permit one target; retain up to five or ten; make count fixed at two.
**Probe:** Placement feasibility was tested at every boundary in every difficulty band; the override gate accepted 5,310/5,310 draws.
**Decision:** Use 2..4 and force at least one horizontal and one vertical target.
**Failure mode avoided:** “Recolor only the first/only target” and orientation-specific shortcuts.
**Limitation:** Single-target lessons are intentionally excluded because they are weaker teaching examples.

## 4. Make distractor count 2..3

**Original rationale:** Imported normal draws had zero distractors; distractors existed only behind degenerate textures.
**Alternatives considered:** One mandatory distractor; four or more distractors; retain degenerate-only controls.
**Probe:** Minimum 8x8 / maximum seven-component construction, all bands, all count boundaries, and 600-draw semantic census.
**Decision:** Always include two decisive negatives and optionally a third varied size-four negative.
**Failure mode avoided:** Positive-only data on which `recolor_all_cyan` is perfect.
**Limitation:** The optional third component changes morphological variety, not the core identifiability requirement.

## 5. Mandatory L-triomino distractor

**Original rationale:** Canonical examples contain non-straight size-three components, but the imported normal generator omitted them.
**Alternatives considered:** Only dominoes; only size-four bent shapes; randomly include an L.
**Probe:** The `l_triomino_unchanged` witness fired 600/600 and refuted `recolor_all_cyan`, `recolor_all_size3_components`, and `recolor_components_at_most_three` in every checked witness case.
**Decision:** Include one L-triomino in every ordinary draw.
**Failure mode avoided:** Learning that size three alone is sufficient.
**Limitation:** Only the four rotations of one L topology are used.

## 6. Mandatory straight domino distractor

**Original rationale:** Canonical examples contain size-two straight components; imported normal draws omitted them.
**Alternatives considered:** Use only longer lines; use a singleton; make the short line optional.
**Probe:** The `short_straight_component_unchanged` witness fired 600/600 and refuted all-cyan, all-straight, and size-at-most-three competitors.
**Decision:** Include one horizontal or vertical domino in every ordinary draw.
**Failure mode avoided:** Learning that straightness or color alone is sufficient.
**Limitation:** Singletons are not generated because they are outside the canonical component-size manifold.

## 7. Include both edge and interior targets

**Original rationale:** No imported positional curriculum was recorded.
**Alternatives considered:** Fully random placement; schedule edge-only examples; expose a position-bias axis.
**Probe:** `edge_and_interior_targets` fired 600/600 and refuted edge-only and interior-only target selectors.
**Decision:** Constrain one mandatory target to touch an edge and another to be interior; swap orientations across four schedule profiles.
**Failure mode avoided:** Position becoming a proxy for the target predicate.
**Limitation:** Other positional shortcuts, such as exact quadrant frequency, are addressed statistically rather than by named witnesses.

## 8. Separate components by cardinal background, allow diagonal contact

**Original rationale:** Imported code used an eight-neighbor clearance, stricter than the 4-connected object semantics.
**Alternatives considered:** Preserve a full one-cell halo; allow cardinal contact; force selected contact profiles.
**Probe:** Component counts round-trip exactly and the rule mirror agrees with all canonical pairs.
**Decision:** Forbid overlap and cardinal contact between components; allow diagonal proximity.
**Failure mode avoided:** Accidental 4-connected merging that changes target/distractor counts.
**Limitation:** Diagonal proximity is not exposed as a public axis.

## 9. Construct with deterministic backtracking

**Original rationale:** Imported implementation used nested retries and could not honor its declared extremes reliably.
**Alternatives considered:** Fixed templates; unbounded retries; rejection sampling; macro-cell packing.
**Probe:** Boundary tests across all bands, determinism test, global RNG isolation test, and override census.
**Decision:** Enumerate legal translations, shuffle them with a label-keyed RNG, and backtrack until every requested component is placed.
**Failure mode avoided:** Silent object omission and seed-dependent placement failure.
**Limitation:** The planner is specialized to these small grids/shapes rather than a general-purpose packing library.

## 10. Expose only recoverable axes

**Original rationale:** Imported metadata listed palette aliases, singleton tokens, and values never used by generation.
**Alternatives considered:** Implement all nine legacy axes; mark some diagnostic; retain texture degenerates.
**Probe:** Static lint, defect lint, `observe_overrides`, and the override checker.
**Decision:** Remove `palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture`; keep only four exact observables.
**Failure mode avoided:** Training/evaluation code believing an override was honored when it had no independent effect.
**Limitation:** There is no public switch for deliberately weak/degenerate examples; such fixtures live only in tests.

## 11. Difficulty skews probabilities, never legality

**Original rationale:** Imported easy/hard branches changed legal ranges, contradicting `AXES.valid`.
**Alternatives considered:** Band-specific axis contracts; no difficulty variation; narrow valid domains.
**Probe:** Every min/mid/max case was tested under `None`, easy, medium, and hard; the after override gate had zero findings.
**Decision:** Each band’s weighted choice list contains every declared value.
**Failure mode avoided:** A valid override crashing only in one difficulty band.
**Limitation:** Difficulty reflects density/count tendencies, not a formal model of human ARC difficulty.

## 12. Broad canonical checker plus stronger ordinary postconditions

**Original rationale:** Imported checker encoded the generator’s positive-only assumptions instead of the task grammar.
**Alternatives considered:** Make canonical checker require every teaching witness; special-case canonical inputs; omit validation.
**Probe:** 5/5 canonical acceptance, 60/60 generated clean, 54/58 destructive mutations rejected, and six explicit mutation fixtures rejected.
**Decision:** `self_check` owns the canonical manifold; `_teaching_errors` enforces the stronger generated curriculum internally.
**Failure mode avoided:** Rejecting lawful canonical distractors or weakening generated lessons to the broadest accepted grammar.
**Limitation:** Some accepted canonical-like grids are intentionally not emitted by normal generation.

## 13. Two examples per lesson

**Original rationale:** Imported generator declared no identifiability contract.
**Alternatives considered:** One, three, four, or five demonstrations.
**Probe:** Every ordinary example independently refutes all ten named rivals; 12/12 two-demo lessons across all bands were identifiable.
**Decision:** Set `EXAMPLES_NEEDED = 2`, the minimum non-vacuous contract allowed by the gate.
**Failure mode avoided:** Overspending context on redundant examples while still permitting a query-changing rival.
**Limitation:** The guarantee is relative to the declared competitor set, not all computable hypotheses.
