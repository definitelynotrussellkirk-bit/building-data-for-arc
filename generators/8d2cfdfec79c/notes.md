# Current account: 8d2cfdfec79c

## Parametric candidate: visible-border selection (owner acceptance pending)

The separate `workspace/parametric/` candidate supports `mode=outline` (exact canonical Racket bytes) and `mode=fill_most_visible`. The alternative first renders all borders, counts surviving pixels, selects the first-appearing color among the maxima, and fills only zero cells strictly inside that color's original bbox. Occlusion can reverse original-perimeter ranking, so the fill target depends on the rendered intermediate. Production source and canonical authority remain unchanged.

Requests support 2–6 demonstrations (default 3), 1–4 queries (default 4), independent counts, matched input streams across modes, and 8..30 × 10..30 canvases with 2–6 paired colors. Four-query episodes include a full-span 30×30 crossing/nested scene. The first two demos teach both visible-count selection and a thin winner, with an interior crossing object whose border must survive filling. Earlier anchors admitted overwrite-interior, smallest-fillable and thin-exclusion shortcuts; the teaching core was repaired without increasing its two-demo minimum.

Current evidence: 47 focused tests; `workspace/parametric/evidence/current/audit.json` covers 18 native jobs, 29 finite rivals, 222 protected-Racket evaluations and zero supported query disagreements. `checks/8d2cfdfec79c/independent-review.json` retains the independent six-seed Python recheck. Native qualification passed both modes at seeds 0 and 17 with three demos/four queries; `checks/8d2cfdfec79c/qualification/` holds its source binding and execution. The protected sequential witness at `checks/8d2cfdfec79c/causal/witness.json` selects color 7 from visible counts {8:20,7:30,2:22}; a raw-perimeter counterfactual selects 8 and changes the final output.

`audit.py` is the reusable task-local Racket/teaching audit. `public_export.py` exposes one selected query only, uses exact visible-byte IDs, rejects duplicate public payloads and keeps future queries/private labels controller-side. See its README for runnable commands. These are finite checks, not universal uniqueness or measured learning gain. Owner exact-source integration, fresh qualification and acceptance remain required; no training admission. Existing canonical evidence below retains its original scope.

## Intended rule and authority

The input is a background-0 ARC grid containing 2–4 nonzero colors. Each active color occurs exactly twice, with its two cells in different rows and columns. Starting from a fresh zero grid, process colors in row-major order of first appearance and draw the border of each color's bounding box; later borders overwrite earlier borders. The Racket authority was not changed. `RULE_HASH = 23e27bc62b89`, and the retained Python `_predict` is diagnostic only.

## Repaired distribution

Version 2.0.0 replaces the old rejection-sampled disjoint-only generator with constructive layouts. The exact public axes are now only values recoverable from returned pixels:

- `grid_h`: 8..13
- `grid_w`: 10..14
- `rectangles`: 2..4
- `layout_kind`: `disjoint`, `nested`, or `crossing`

Every Cartesian combination is constructive in every difficulty band and round-trips through `observe_overrides`. Unknown keys, Boolean/coercible integer values, out-of-range values, and invalid layout names fail closed. Default dimensions cycle through the five canonical shape anchors in every band; a band offset prevents byte-identical difficulty streams without narrowing legal overrides.

The validator now accepts lawful overlap, including canonical pair 3. The retained minimal case is `counterexamples/canonical_crossing_rectangles.json`. It rejects non-ARC scalar values, wrong multiplicity, collinear pairs, canvases outside the declared domain, and fewer than two or more than four active colors.

## Curriculum and semantic witnesses

The four-position default schedule is:

1. two crossing rectangles — overwrite/order witness;
2. two disjoint rectangles — separated canonical-style witness;
3. three crossing rectangles with a two-cell side — overwrite, first-two-only, and minimum-side witnesses;
4. three nested rectangles with a two-cell side — containment, first-two-only, and minimum-side witnesses.

A generated lesson contains three demonstrations and one query. Any query rotation leaves at least one order/occlusion witness and at least one 3-rectangle thin-side witness in the remaining demonstrations. Executable rivals cover identity, filled boxes, fixed color 8, reversed first-appearance order, completion order, restoring clue cells, using only the first two colors, and ignoring boxes with a side below three.

## Reversed prior choices

- **Overlap:** the old invariant required disjoint rectangle footprints. This contradicted a canonical input. Overlap is now lawful and explicitly taught.
- **Axes:** the old generic `palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture` controls were dead, aliases, or non-observable; `rectangles` also advertised values the validator rejected. They were removed rather than simulated.
- **Degenerates:** fixed invalid fixtures are no longer ordinary axis values. Invalid structures belong in tests, not the production training distribution.
- **Schedule:** the first repaired three-position schedule passed ordered lessons but produced 220 ambiguous query rotations in 1,200 tested rotations. It was replaced by the four-position redundant-witness schedule; the final 1,200-rotation census had zero declared-rival ambiguities.

## Evidence and limits

Final generator SHA-256: `812ba798adc00230ffea4b7b6ae8e21c7bdcb6e5063e6083771a14e2c77d9220`.

- Official final battery: 12/12 stages green under `checks/after-final3/`.
- Focused portable tests: 129 passing under `checks/task-tests-final4/`.
- Random lesson census: 300 lessons, 1,200 labeled pairs, and 1,200 query rotations; zero materialization/scoring errors and zero declared-rival ambiguities under `checks/lesson-census-final2.json`.
- Exhaustive declared-period census at seed 0: all 12 band/start lessons and 48 query rotations passed under `checks/lesson-census-period2.json`.
- Fresh-packet replay: the exact four-file patch applied cleanly, reproduced generator SHA-256 `812ba7…9220`, and passed 129 focused tests under `checks/fresh-replay/`.

These are finite checks against the declared rivals, not proof of unique induction against every possible rule. Default shapes intentionally retain canonical anchors rather than exhaust the full size rectangle uniformly; the full exact size domain remains available through overrides. No open blocker remains for this task-local repair.
## Current reviewer considerations

Source SHA-256: `812ba798adc00230ffea4b7b6ae8e21c7bdcb6e5063e6083771a14e2c77d9220`.

# Decisions for 8d2cfdfec79c

## D1 — Keep the Racket authority unchanged

**Choice.** Preserve the existing rule and pin normalized hash `23e27bc62b89`.

**Why.** All five canonical labels are internally consistent: draw each color's bounding-box border on a blank canvas in row-major first-appearance order, with later colors overwriting. The failure was in generator ownership and teaching data, not the authority.

**Rejected alternative.** Relax or rewrite the Racket implementation to match the old disjoint-only description. That would erase an authority-owned overlap case and change labels without evidence.

**Probe.** `_predict` matches all five canonical pairs; final rule smoke and authority sync are green.

## D2 — Admit lawful overlaps

**Choice.** Remove the old footprint-disjointness restriction from `self_check`; expose `layout_kind` values `disjoint`, `nested`, and `crossing`.

**Why.** Canonical pair 3 contains two non-comparable overlapping bounding boxes. Its later color overwrites the earlier border at intersections. Rejecting it made the validator narrower than the task.

**Failure mode considered.** Two clue cells may not collide in the input, and each color must still occur exactly twice in distinct rows and columns. The constructive layouts enforce these constraints.

**Evidence.** `counterexamples/canonical_crossing_rectangles.json`; canonical ownership test; final self-check/profile-floor stages.

## D3 — Declare only exact, observable controls

**Choice.** Public axes are `grid_h` 8..13, `grid_w` 10..14, `rectangles` 2..4, and `layout_kind` in three values. Every combination is valid in every band and recovered by `observe_overrides`.

**Why.** The prior `palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture` controls were aliases, dead, or not recoverable. The previous `rectangles` axis claimed 1..8 while generation and validation accepted much less. This inflated the override matrix and silently mislabeled metadata.

**Rejected alternatives.** (a) Retain generic axes as no-op compatibility aliases; this preserves dishonest metadata. (b) Declare many incompatible combinations; constructive geometry makes that unnecessary. (c) Keep invalid fixed degenerates in the ordinary texture domain; invalid cases belong in tests.

**Probe.** Focused Cartesian test covers 3 bands × 4 shapes × 3 counts × 3 layouts; official override stage is green.

## D4 — Construct rather than reject-sample

**Choice.** Use deterministic relation-specific builders: quadrant tiles for disjoint boxes, containment chains for nested boxes, and engineered non-comparable overlaps for crossing boxes.

**Why.** The old sampler exhausted attempts for legal overrides and introduced heavy rejection bias. The new builders realize every requested semantic state directly, then assert that observed pixels equal the requested controls.

**Failure mode considered.** Four nested rectangles on the minimum 8×10 canvas need a valid innermost rectangle. The last box is explicitly two rows high and strictly inside its predecessor. Four crossing rectangles use a central containment subchain while the first two remain crossing.

## D5 — Preserve canonical profiles in every band

**Choice.** Default dimensions cycle through `(8,10)`, `(9,11)`, `(9,12)`, `(10,12)`, and `(11,13)`. Easy/medium/hard use different offsets into that cycle; legal override domains stay identical.

**Why.** The profile floor requires genuine canonical size/palette support, while the dead-band detector requires difficulty to enter sampling. Offsetting a common canonical schedule satisfies both without clamping overrides.

**Rejected alternative.** Use disjoint band-specific size intervals. That caused legal values to fail in some bands and made exact overrides dishonest.

## D6 — Teach overwrite order explicitly

**Choice.** Crossing scenes put color A's first clue before color B's first clue, but complete B before A; B's border overwrites an A clue. This separates first-appearance order from reverse order, completion order, and clue restoration.

**Why.** Correct labels alone do not teach the ordering rule when rectangles do not intersect. The canonical data includes overlap, so generated demonstrations should expose it deliberately.

**Executable rivals.** Identity, fill boxes, fixed color 8, reverse order, completion order, restore clues, first two only, and minimum side three.

## D7 — Replace the three-position schedule after rotation evidence

**Initial choice.** A three-step schedule used disjoint-2, crossing-2, nested-3. It refuted every declared rival in the normal ordered 3-demo lesson and passed the standard semantic battery.

**Counterevidence.** `checks/lesson-census-failure-summary.json` found 220 ambiguous query rotations among 1,200. Holding out the only crossing or 3-rectangle example let order, restore-clue, or first-two rivals fit every remaining demonstration while changing the query.

**Final choice.** Four positions: crossing-2, disjoint-2, crossing-3-thin, nested-3-thin. Any held-out pair leaves an order witness and a 3-rectangle thin-side witness among the three demonstrations.

**Evidence.** A focused cyclic-rotation regression, random census `checks/lesson-census-final2.json` (0/1,200 ambiguous rotations), and fixed-seed period enumeration `checks/lesson-census-period2.json` (0/48).

## D8 — Scope and residual uncertainty

The final claims are limited to the declared task domain, the eight executable rivals, 300 randomly sampled lessons, and all declared schedule starts at one fixed seed. Unknown adversarial rules may still fit finite demonstrations. Defaults favor canonical shape anchors; uniform coverage of the full dimension rectangle is not claimed, though every exact override is supported and observed.
