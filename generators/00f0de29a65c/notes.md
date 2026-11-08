# Working notes: 00f0de29a65c

## Review source and baseline

The selected baseline was version `2.1.0`, SHA-256 `3c2023001d64445d5212c29e440722310ba312c0a90b5e0f2182413c2ce1496d`. The prior unverified audit in `evidence/review_index.json` was used only as a lead: it reported that `texture="plain"` could still produce a minimum-size tie and that easy mode ignored `n_shapes=4`. Both were reproduced independently before repair.

Additional baseline findings were: missing `RULE_HASH`; ordinary texture values overlapping advertised degenerates; `plain` being byte-identical to the default stream; degenerate fixtures passing `self_check`; unknown or unsupported exact controls being ignored or inconsistently rejected; only 1/60 canonical-profile hits with 0/20 in easy and hard; and no executable semantic lesson contract. The canonical Racket rule itself passed real execution and was not changed.

## Selected repair

Version `3.1.0` is a deliberate distribution/contract break:

- Replaced contradictory texture aliases with three observable semantic profiles: `unique_min`, `two_way_tie`, and `all_tied`.
- Made `grid_h`, `grid_w`, `n_shapes`, and `texture` exact, validated axes; rejected unknown keys and the single impossible combination `two_way_tie + n_shapes=2`.
- Replaced rejection-heavy free placement with constructive corner slots, connected sparse polyomino libraries, distinct colors, and an isolated marker.
- Anchored default dimensions and size profiles to the five canonical examples while retaining override range coverage.
- Added strict final-grid analysis, `observe_overrides`, `strict_canonical_like`, an input-pure Python `rule_mirror`, seven original rivals/witnesses, and the `fixed_size_five` canonical shortcut probe.
- Added `workspace/lesson_probe.py`, which labels with a separate component parser/oracle and dynamically audits every declared competitor, shortcut, and witness.

## Required self-review and second repair pass

The first repaired version (`3.0.0`, generator SHA `6e4d625540c9ae979bcee4285e99f1401c38e9feaae7354ef8d460adf957af9c`) passed all 12 battery stages, but a final shortcut review found that `unique_min` always selected the bottom-left slot and tied profiles always selected the first scanned object. A profile-conditioned positional rival therefore remained a substantial shortcut without learning size selection: an independent replay matched 1,256/1,500 examples and survived 133/300 four-demo lessons (`checks/profile_position_v3.0_reproducer.json`).

Version `3.1.0` rotates the unique minimum through all four quadrants and makes every two-way-tie example put a larger distractor before both minima in scan order. The old shortcut is retained as `LESSON_COMPETITORS["profile_position"]` with witness `profile_position_conflict`. RED evidence is `checks/tdd_red_position_curriculum.log`; the final 300-lesson census refutes it in 300/300 lessons.

## Final measured limits

The default prior intentionally stays close to the canonical task: exactly three shapes, five canonical dimension profiles, a four-slot semantic schedule, corner-separated objects, and sizes from the retained 3–8-cell library. Exact overrides exercise 2–4 shapes and wider dimensions, but this is not a claim of universal induction over arbitrary connected-component scenes. The marker may occur anywhere outside object bounding boxes; objects remain corner-separated to guarantee construction and clean component identity.

Final selected generator SHA-256: `c5938d66d45b9336ab74f2d0de6ef1ea02faba784a3e56342f84148fb2bc8171`. Canonical Racket authority unchanged; pinned rule hash `708518128a6f`.
## Current reviewer considerations

Source SHA-256: `c5938d66d45b9336ab74f2d0de6ef1ea02faba784a3e56342f84148fb2bc8171`.

# Decisions for 00f0de29a65c

## D1 — Preserve the selected Racket authority

**Input and rationale.** The canonical rule hash is `708518128a6f`; all five canonical pairs and 120 baseline real-Racket applications executed correctly. The defect was in the sampler and contracts, not the label authority.

**Decision.** Pin `RULE_HASH` and leave canonical Racket bytes unchanged. Add an independent Python mirror only for probes.

**Rejected alternative.** Rewriting the Racket rule would add authority risk without addressing dead axes or shortcut-bearing lessons.

**Probe / limitation.** Final rule smoke compares 120 generated inputs against real Racket, and the task-local census compares the Python mirror with a second independent oracle. Neither proves behavior outside valid ARC grids.

## D2 — Replace aliases and negative fixtures with three lawful semantic profiles

**Original rationale.** The imported `plain`, `size_tie`, and degenerate texture surface appears to have been intended to diversify examples and provide negative fixtures, but no retained rationale explains why negatives shared the ordinary axis domain.

**Decision.** The only texture values are `unique_min`, `two_way_tie`, and `all_tied`. Negative fixtures are not training-axis values. Profile identity is inferred from the returned grid and must exactly match the request.

**Rejected alternatives.** Keeping `plain` as an alias was rejected because it was byte-dead and did not guarantee uniqueness. Keeping `tied_smallest` as a “degenerate” was rejected because ties are central lawful evidence for the canonical tie-break.

**Probe / limitation.** Strict defect lint, override matrix, and task tests exercise all values. Profiles encode minimum-count structure but do not enumerate every possible shape-size multiset.

## D3 — Make every advertised control exact and fail closed

**Decision.** `grid_h` 10–18, `grid_w` 11–18, `n_shapes` 2–4, and the texture profile are exact. Unknown keys and wrong types fail; `two_way_tie + n_shapes=2` is declared incompatible because exactly two minima plus a larger distractor requires at least three shapes.

**Rejected alternative.** Silently clamping controls by difficulty was rejected because it recreates the baseline easy-band `n_shapes` failure.

**Probe / limitation.** Final override gate covers 18,810 draws, 18,720 accepted cases, 209 cases, and 90 explicit incompatibility rejections. Difficulty changes deterministic RNG tags/default dimensions but does not narrow exact override validity.

## D4 — Use constructive separated placement

**Decision.** Place connected sparse polyominoes in four nonoverlapping 4×4 corner slots and choose an isolated singleton marker outside every shape bounding box. Use a finite dihedral shape library for sizes 3–8.

**Rationale.** This guarantees exact shape count, connectivity, no accidental merging, a real gap around the marker, and bounded generation time.

**Rejected alternatives.** Rejection sampling on arbitrary positions risked count drift and timeouts. Filled rectangles were rejected because they erase the crop-hole distinction and let `bbox_fill` survive.

**Failure modes / limitation.** Corner separation is a real domain restriction. Exact overrides widen shape count and dimensions, but the generator does not represent arbitrary crowded component layouts.

## D5 — Anchor defaults to canonical linked profiles

**Decision.** Cycle the five canonical dimension/palette profiles, default to three shapes, and use canonical `(5,5,5)` or `(5,5,7)` size profiles in three of every four examples. The unique-min example deliberately uses `(3,5,7)` to teach size selection and refute fixed-size-five.

**Rejected alternatives.** Matching only marginal area/object counts was insufficient: the baseline morphology gate was green while exact linked support was 1/60 with zero easy/hard hits.

**Probe / limitation.** Final profile floor is 60/60 with 20/20 per band. The large census reports 1,125/1,500 strict canonical-like inputs; the remaining 375 are intentional unique-min evidence.

## D6 — Four-example schedule plus executable semantic contract

**Decision.** Use `unique_min, two_way_tie, all_tied, two_way_tie` and retain executable rivals for largest, scan order, reversed tie-break, source-color retention, no upscale, bbox fill, fixed size five, and profile-conditioned position. `lesson_identifiable` requires every rival to be visibly refuted by the four demonstrations.

**Rejected alternative.** Witness-frequency-only testing was rejected because individual examples can contain evidence while a complete lesson still lets a rival survive.

**Probe / limitation.** The final independent census covers 300 lessons/1,500 unique inputs, all bands, and refutes every declared rival in 300/300 lessons. This supports this rival set and sampler; it is not universal induction evidence.

## D7 — Rotate semantic roles after the first green battery

**Finding.** Version `3.0.0` passed 12/12 battery stages but fixed the unique minimum at bottom-left. The independently replayed positional rival matched 1,256/1,500 examples and survived 133/300 lessons.

**Decision.** In `3.1.0`, rotate unique minima through all four quadrants. In every two-way-tie example, put the only occupied top-slot object at size 7/8 and both size-5 minima in lower slots, so scan order visibly selects the wrong object. Declare the old shortcut as a rival and witness.

**Rejected alternative.** Merely randomizing positions was rejected because chance can leave entire short lessons uninformative. The deterministic schedule guarantees refutation at every cyclic start.

**Probe / limitation.** RED: `checks/tdd_red_position_curriculum.log`. Green: `checks/tdd_green_position_curriculum_candidate.log`; final 70-test task suite and large census. Tied minima still use separated corner slots, so the domain is controlled rather than exhaustive.

## D8 — Retain a reusable independent census tool

**Decision.** Keep `workspace/lesson_probe.py` and tests. It loads canonical pairs independently, computes labels through its own component parser, hashes all source inputs, and discovers semantic declarations dynamically.

**Rejected alternative.** Hard-coding rival names in an external one-off script would silently go stale when the generator contract changes.

**Probe / limitation.** The tool's small 12-lesson test and full 300-lesson run are retained. It trusts generator-provided rival functions for rival outputs, but not for the ground-truth labels.
