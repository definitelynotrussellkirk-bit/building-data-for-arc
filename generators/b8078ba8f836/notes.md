# Working notes: b8078ba8f836

## Current intended rule

For every nonzero color occurring exactly twice, fill the inclusive horizontal or vertical segment joining the two cells when they are aligned. An unaligned pair and any color with a count other than two are unchanged. The selected Racket authority was not edited; its pinned hash is `48fc6f20bbde`.

## Review reversal

The imported `2.2.0` sampler required endpoint distance at least three, expected two or more pairs in ordinary scenes, and therefore rejected three of five official inputs, including legal one-gap segments. It also declared nine controls while honoring only dimensions indirectly; helpful textures were byte-identical, degenerate textures occupied the normal domain, unknown keys were swallowed, and no semantic lesson contract existed.

Version `3.0.0` replaces that design with six pixel-observable axes:

- `grid_h=8..12`, `grid_w=8..14`
- `n_horizontal_pairs=1..2`, `n_vertical_pairs=1..2`
- `n_singletons=0..2`
- `distractor_profile=canonical|counterexample`

Every declared combination is constructive, including the 8x8 maximum-content corner. Exact-two pair segments reserve their whole future painted interval, so pairs cannot cross and distractors cannot be overwritten.

## Teaching policy

`EXAMPLES_NEEDED=3`. The sample-index schedule has period three: `canonical, counterexample, counterexample`. Every counterexample scene contains:

1. one exact-two diagonal color, refuting “connect any equal pair with an L”; and
2. one three-cell color with exactly one aligned subpair, refuting “connect aligned cells regardless of total count.”

Thus every consecutive four-pair lesson, and every single-query holdout of it, retains at least one demonstration that refutes both declared canonical shortcuts. The retained fixture is `counterexamples/exact_count_and_alignment.json`; `workspace/build_counterexample.py` regenerates it from the recorded seed.

## Canonical support and validation

`self_check` accepts all five canonical inputs, including endpoint distance two, and rejects malformed count/profile/segment-overlap cases. `strict_canonical_like` retains all official shapes and the scheduled 8x8/three-color anchor. The anchor was changed from a rotating width to 8x8 after the first after-phase profile-floor run showed zero exact hard-band hits.

## Evidence and limits

Final generator SHA-256: `f24df53496b996e4f10bebb978ce798975d4a51606a5f4621a4a80c4cf666521`.

Task tests cover canonical parity, all override boundary combinations in all bands, invalid controls, deterministic/fresh returns, destructive mutations, retained counterexamples, the period-three schedule, and all cyclic four-pair query rotations. The larger retained census sampled 300 lessons (100 per band), 1,200 unique pair inputs and 1,200 rotations with no ambiguity against the two declared rivals.

These are finite checks against named alternatives, not a proof of unique induction against every possible rule. Generated dimensions begin at 8 although canonical validation deliberately accepts official 6- and 7-row inputs. Colors are semantically interchangeable, but each semantic group receives a distinct color to keep count predicates observable.
## Current reviewer considerations

Source SHA-256: `f24df53496b996e4f10bebb978ce798975d4a51606a5f4621a4a80c4cf666521`.

# Decisions — review-da3022f9173fbb7a

## D1 — Keep the selected rule; replace the input sampler

**Original choice/rationale:** Imported rationale was not retained beyond comments. The old source sampled aligned pairs and singleton distractors, but imposed a non-authoritative gap ≥3 and difficulty-specific pair counts.

**Decision:** Leave the canonical Racket program unchanged and pin `RULE_HASH="48fc6f20bbde"`. Replace only the Python input generator and its authoring contract.

**Evidence:** The canonical program matches all five labeled pairs. Before repair, rule smoke already applied successfully 120/120 times, while `self_check` rejected canonical pairs 0, 1, and 4. This isolates the defect to the sampler/validator rather than the authority.

**Alternative rejected:** Editing the Racket rule to match the old gap/count assumptions would contradict the labeled task.

## D2 — Use only exact, pixel-observable axes

**Decision:** Reduce nine mostly inert controls to six exact controls: dimensions, horizontal-pair count, vertical-pair count, singleton count, and semantic profile. Reject unknown keys and invalid types/ranges before construction; expose `observe_overrides`.

**Reason:** The prior API accepted typoed keys, ignored palette/alignment/texture controls, and had singleton domains that could not demonstrate an effect. A smaller truthful API is more useful than a large nominal combinatorial reach.

**Probe:** The task suite checks every boundary Cartesian corner across `None/easy/medium/hard`; the native override gate checks all 197 cases over 17,730 draws.

**Failure mode considered:** The densest 8x8 combination needs eight distinct semantic colors. Construction uses all available nonzero colors at that corner and fails loudly rather than silently shortening a requested count.

## D3 — Teach both hidden predicates in the ordinary curriculum

**Decision:** Add a `counterexample` profile containing both a diagonal exact-two pair and a three-cell color with one aligned subpair.

**Reason:** Canonical examples alone are fit by two plausible wrong rules: connect diagonal pairs with an L, or ignore the exact-count condition. A singleton only teaches `count != 1`; it does not teach `count == 2` against count three.

**Alternative rejected:** Keeping negative fixtures only behind a diagnostic texture. That would make labels correct but ordinary lessons semantically ambiguous.

**Limitation:** The two rivals are high-value hypotheses, not an exhaustive hypothesis class.

## D4 — Use a period-three schedule and support arbitrary single-query rotation

**Decision:** `canonical, counterexample, counterexample` with three demonstrations and one query.

**Reason:** Every four-consecutive-pair window has at least two counterexample pairs. Holding out any one pair leaves at least one counterexample demonstration, so both named rivals are still refuted.

**Probe:** Exhaustive local tests over consecutive starts and all four holdouts; required-rotation semantic gate found 0/48 ambiguous; 100-lessons-per-band census found 0/1,200 ambiguous rotations.

**Alternative rejected:** Purely random counterexample frequency, which can produce an all-positive lesson even when pooled witness rates look healthy.

## D5 — Anchor canonical distribution support explicitly

**Initial decision:** Rotate canonical-profile widths 8, 9, 10, 11.

**Reversal:** After the first after-phase profile-floor run had exact support in easy/medium but zero in hard, canonical scheduled draws were anchored to `(8,8,3 colors)`, an exact official profile.

**Evidence:** The retained failure is `checks/after-profile-floor/`; the passing rerun is `checks/after-profile-floor-2/` and the final battery repeats the pass.

**Tradeoff:** Canonical scheduled shapes are less varied, while the two counterexample slots retain the full dimension domain and randomized layout.

## D6 — Make validators diagnostic and authority-aligned

**Decision:** Accept endpoint distance two; require at least one eligible pair of each orientation in generated grammar; detect pair-segment intersections, blockers, malformed triplets, bad colors/shapes, and profile mismatch. Keep color-role swaps valid.

**Reason:** The old validator encoded sampler habits as task law and rejected official inputs. The new validator distinguishes semantic structure from arbitrary color identities.

## D7 — Retain one source-bound minimal counterexample bundle

**Decision:** Store `generators/b8078ba8f836/counterexamples/exact_count_and_alignment.json` and regenerate it with `workspace/build_counterexample.py`.

**Reason:** It captures the exact intended output and both rival outputs, making the semantic repair reproducible without copying a full census.

**Limit:** The fixture is one lawful scene. Population evidence remains in the semantic gate and lesson census reports.
