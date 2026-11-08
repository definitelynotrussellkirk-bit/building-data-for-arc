# Working notes: 6eb3835a5555

## Intended rule

Color 5 cells are walls. A **room** is a four-connected component of non-5 cells. If the nonzero, non-5 cells in a room use exactly one distinct color, all zero cells in that room are filled with that color. Empty rooms and rooms containing two or more distinct seed colors are unchanged. The selected canonical Racket authority remains unchanged at rule hash `2944822b1e33`.

## Reversed design choices

Version 2.0.1 described a fixed rectangular 2×2 chamber task with one distinct marker per chamber while its sampler actually varied rectangular grids, exposed nine mostly inert axes, and treated invalid negative fixtures as ordinary textures. That design omitted two canonical semantics: partial walls can create merged/nonrectangular rooms, and multiple cells of the same color still count as one distinct color.

Version 3.0.0 replaces those controls with one exact, observable `scene_profile` axis over six finite wall geometries. Four profiles preserve the two exact canonical size/palette signatures; two larger profiles provide structural variation. Unknown controls, invalid profiles, invalid difficulty values, booleans/floats/strings for integer controls, and negative seed/sample indices fail closed.

## Teaching decision

The strongest shortcut fitting all three canonical pairs is “fill only rooms containing exactly one seed **cell**.” Every ordinary draw now includes a room with two same-color seed cells, which the intended rule fills and that shortcut leaves unchanged. Every draw also includes a room with conflicting colors, refuting first-seed and last-seed flooding. The exact generated witness is stored in `counterexamples/repeated_same_color_shortcut.json` and is covered by the focused seed/profile test.

Lessons use three demonstrations and one query. The deterministic sampler schedule has period six through the profile sequence; every individual ordinary grid contains both semantic witnesses, so all cyclic starts and query rotations refute the declared rivals. A 300-lesson census (100 per difficulty band) materialized 1,200 unique labelled pairs and checked 1,200 query rotations with zero declared-rival ambiguities or scoring/materialization errors.

## Assumptions and limits

- Walls and seed colors retain their canonical roles; no palette permutation of gray/background is attempted.
- The sampler deliberately uses six audited geometries rather than claiming arbitrary wall-maze coverage.
- The semantic contract is finite. The census’s generic measured-label mutations occasionally report `first_object_only`/`topmost_object_only` ambiguity; those candidates use known Racket-labelled outputs and are not independent unseen-input solvers, but their records remain a reminder that declared-rival success is not universal identifiability proof.
- Generation remains unapproved for training until maintainer acceptance; this review does not change approval metadata.

## Evidence

Final generator SHA-256: `1f42e65ea5b8ce51fcd9035201ceb73311a00ad64408e6f76ad6f732f9b385bf`. The final 12-stage battery and 23 focused tests are green. Leads from retained returns `review-8dde258cde80eac5-v0001` and `review-a9c6435c422ea287-v0001` were reproduced against the selected baseline before repair rather than accepted as current measurements.
## Current reviewer considerations

Source SHA-256: `1f42e65ea5b8ce51fcd9035201ceb73311a00ad64408e6f76ad6f732f9b385bf`.

# Decisions: 6eb3835a5555

## D1 / G-001 — Keep the Racket authority; repair the generator model

**Original rationale:** unknown. Version 2.0.1’s comments said rectangular chambers with one marker each, while the canonical examples and rule permit connected rooms formed by partial walls, repeated same-color seeds, conflicts, and empty rooms.

**Alternatives considered:** (a) patch only `SUMMARY`, `RULE_HASH`, and override plumbing; (b) generate arbitrary wall mazes; (c) use a small audited family of connected-room geometries. Metadata-only repair would leave the teaching defect. Arbitrary mazes would increase validator and distribution risk without evidence that it improves this task.

**Decision:** preserve the selected canonical Racket authority and implement a Python connected-component mirror. Select option (c): six deterministic wall profiles, all interpreted through four-neighbor non-gray components. Probe: the mirror matches all three canonical pairs and the final Racket `rule_smoke`/`authority_sync` stages are green. Failure mode: the finite profile family is not arbitrary-maze coverage; this is stated as a limit rather than hidden.

## D2 / G-001 — Replace nine stale axes with one exact profile control

**Original rationale:** the old metadata listed `grid_h`, `grid_w`, `palette_kind`, `n_chambers`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture`; most were constants, aliases, or ignored. The baseline override matrix produced 2,121 findings across 9,990 draws, including requested widths/heights not observed and an accepted unknown key.

**Alternatives considered:** preserve the old axis surface and implement every cross-product; keep only separate height/width axes; expose no controls. The first adds many incompatible combinations, the second cannot identify partial-wall geometry, and the third gives no exact profile probe.

**Decision:** expose only `scene_profile`, with six enumerated values and `observe_overrides()` based on exact wall signatures. Reject unknown keys and invalid values. Validate seed/sample index with `type(value) is int` and nonnegative bounds; validate difficulty explicitly. Probes: final override and defect-lint stages are green; each profile has a deterministic focused test. Failure mode: adding a profile requires updating metadata, signatures, tests, and schedule together.

## D3 / G-002 — Put both semantic witnesses in every ordinary grid

**Original rationale:** the old sampler placed one seed cell in every chamber, so it could never distinguish “one seed cell” from “one distinct seed color,” and it omitted conflict behavior in ordinary draws.

**Alternatives considered:** place the repeated-same-color and conflict witnesses only once per lesson; use negative/degenerate textures; include both in every grid. Lesson-only placement is vulnerable to query rotation. Negative fixtures are not ordinary lawful training examples.

**Decision:** every ordinary grid contains (1) a room with at least two occurrences of one color, and (2) a room with at least two distinct seed colors. Canonical-size profiles also include another singleton-color room. The generator declares executable rivals for exactly-one-cell, first-seed, and last-seed rules, plus witness predicates and a `lesson_identifiable` hook. Probe: the exact seed 419/profile `canonical_7x9` counterexample is Racket-labelled and checked in the focused suite. Failure mode: this guarantees only the declared finite rivals, not every imaginable hypothesis.

## D4 / G-001 — Use four canonical anchors and two structural anchors

**Original rationale:** baseline profile-floor and semantic checks were advisory because the sampler did not reliably hit exact canonical size/palette support and its coarse object signatures diverged.

**Alternatives considered:** only reproduce canonical grids; use only large rectangular grids; combine exact canonical anchors with larger structural variants. Canonical-only support would overfit shape. Large-only support failed profile-floor expectations.

**Decision:** schedule four exact-size profiles (`canonical_7x9`, `canonical_7x8`, `canonical_7x9_t`, `canonical_7x8_l`) and two larger profiles (`wide_9x13`, `tall_13x10`). The larger profiles use separated same-color markers and a conflict pair to overlap public coarse marker/object signatures while remaining lawful. Difficulty changes keyed placement randomness (`seed_layout_<band>`) but not the semantic curriculum. Probes: each 20-draw band hits both official profiles; distribution/profile-floor/diversity/grammar stages are green.

## D5 / G-003 — Test behavior through the portable public runtime

**Original rationale:** no selected task-local tests existed for the actual contract. Historical audit findings were useful leads but were bound to earlier returns and could not stand in for current-source measurements.

**Decision:** write focused tests before source changes and run them through `arcpuzzles check --stage task_tests`. The red run on baseline bytes had 22 failures and 1 pass; the final portable run has 23 passes. Tests cover canonical parity, exact axis metadata, every profile override, invalid controls, canonical-profile support by band, both witnesses on default draws, canonical shortcut fit/disagreement, all query rotations for a generated lesson, deterministic fresh outputs, and global-RNG purity.

**Failure mode:** the focused finite seeds do not replace the repository battery or census, so both were run separately. The test uses `reviewer_support.find_root` and `canonical_pairs`, avoiding the portability defect found in audit A-158-001.

## D6 / G-002 — Interpret the 300-lesson census narrowly

**Decision:** use three demonstrations and one query, production order from consecutive sampler indices, and required hold-out of every labelled pair once. The 300-lesson report covers 100 lessons per difficulty band, 1,200 labelled pairs, 1,200 unique normalized inputs, and 1,200 query rotations. Every declared rival was refuted in every production lesson and rotation; materialization, scoring, and hook errors were zero.

**Limit:** the report explicitly says it is a finite declared-rival census, not proof of identifiability. Its generic candidates are measured-label mutations, not independent rules for unseen grids; rare object-attribution ambiguities are retained rather than promoted into the declared task-domain contract. Future work could add an independent searched-rival provider if a concrete plausible rule is identified.

## D7 — Prior audit leads

I used retained returns `review-8dde258cde80eac5-v0001` and `review-a9c6435c422ea287-v0001` only as leads. Their counterexamples motivated reproduction of the repeated-same-color and conflicting-color omissions. The before battery and new TDD red run established those defects on the immutable selected baseline before any repair.
