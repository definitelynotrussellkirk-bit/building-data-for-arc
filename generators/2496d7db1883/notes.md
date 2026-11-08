# Working notes: 2496d7db1883

## 2026-10-02 review `review-e85b4619a4096b9c`

- Baseline battery: 6 green, 2 advisory, 4 failed. Failures were lint, Racket smoke (33-wide OOB grids), strict defect lint, and override contract (8,495 findings; unknown keys accepted).
- Canonical shortcut found: both training demonstrations map query rooms to key colors in reverse reading order; the test maps them in the same order. Therefore “always reverse the example colors” fits every demonstration but fails the test.
- Rebuilt generator as version 3.0.0 around exactly four rooms, two keys, two queries, bounded room sizes, and seven observable axes.
- Added an eight-profile lesson schedule covering row/grid, grouped/interleaved roles, same/reverse mappings, and different-shape/same-shape-shifted motifs.
- Added robust room analysis, strict checks, override observer, Python answer mirror, executable rivals, semantic witnesses, lesson identifiability, and mutation fixtures.
- Added 12 regression tests. TDD regressions first reproduced illegal width, unknown-key acceptance, missing semantic APIs, shortcut survival, and the medium profile-floor hole.
- First revised battery: 11 green, profile floor failed because medium had no exact canonical profile. Medium `room_h` now samples uniformly over 3..5 while easy/hard retain difficulty skew.
- Final battery on generator SHA `44e2cd249e877dc3f3cacaf803623f44cd89fbd20eaac0047a72d6c3c7ede051`: 12/12 green, 600/600 strict semantic samples, 12/12 identifiable lessons, 12,870/12,870 override draws accepted, 0 findings.
- Racket authority was not changed: canonical replay, smoke, sync, and execution parity all pass.
- Remaining deliberate limits: wall color fixed to 1 for generation; exactly four rooms; generated room width <=6 to keep row grids <=30; canonical 7x33 test is accepted but not ordinarily generated.
## Current reviewer considerations

Source SHA-256: `44e2cd249e877dc3f3cacaf803623f44cd89fbd20eaac0047a72d6c3c7ede051`.

# Design decisions for `2496d7db1883`

## Decision standard

A public input choice was kept only when it is lawful, changes the returned grid, can be recovered by `observe_overrides`, and helps either canonical coverage or semantic disambiguation. Choices that were constants, dead aliases, negative fixtures, or mere implementation diagnostics were removed from `AXES`.

## Input and architecture decisions

### Four rooms; two keys and two queries

- **Original state/rationale:** the old code varied row/column counts, but its rationale was not recorded. It commonly paired a key and query in each column.
- **Decision:** generate exactly four equal wall-separated rooms with two example rooms and two query rooms.
- **Alternatives considered:** retain arbitrary `n_rows/n_cols`; allow three or more mapping pairs.
- **Probe/evidence:** all canonical inputs contain four rooms and two mappings. Variable columns caused 33-wide illegal grids and made same-column copying a perfect shortcut.
- **Failure mode prevented:** output sizing failures and positional leakage.
- **Limitation:** larger mapping systems are not covered.

### `layout = row|grid`

- **Original state/rationale:** the old arrangement was effectively column-paired; position variation did not break the alignment shortcut.
- **Decision:** expose row and two-by-two grid layouts as real observable alternatives.
- **Alternatives considered:** arbitrary mosaics or a fixed canonical row only.
- **Probe/evidence:** canonical inputs include both one-row and two-by-two arrangements. Both values fire in each eight-profile cycle and in every semantic census band.
- **Failure mode prevented:** assuming one board topology or one same-column pairing.
- **Limitation:** only regular equal-room partitions are generated.

### `role_order = grouped|interleaved`

- **Original state/rationale:** keys and queries followed a fixed positional relationship.
- **Decision:** use `K,K,Q,Q` or `K,Q,K,Q` in reading order.
- **Alternatives considered:** all six two-key/two-query permutations.
- **Probe/evidence:** the chosen pair is sufficient to break nearest-room and fixed-region shortcuts while keeping lessons readable. `interleaved_spatial_counterexample` fired 153/600 times.
- **Failure mode prevented:** classifying room role from a fixed half/row/column.
- **Limitation:** not every combinatorial role permutation is represented.

### `mapping_order = same|reverse`

- **Original state/rationale:** both canonical training examples happen to use reverse order; the canonical test uses same order. The old generator did not deliberately balance this disagreement.
- **Decision:** schedule both same and reverse mappings in every four-profile lesson window.
- **Alternatives considered:** random permutation only; always canonical-training reverse order.
- **Probe/evidence:** the reverse-order rival fits both canonical demonstrations and fails the canonical test. Final semantic census: same 302/600, reverse 298/600.
- **Failure mode prevented:** answering from color order without inspecting motifs.
- **Limitation:** with two pairs, the only permutations are same and reverse.

### `motif_relation = different_shapes|same_shape_shifted`

- **Original state/rationale:** motifs were sampled, but the distribution did not explicitly separate normalized shape from exact room-relative position.
- **Decision:** half the schedule uses distinct normalized shapes; half uses the same normalized shape at two distinct room-relative offsets.
- **Alternatives considered:** different shapes only; arbitrary motifs without a controlled relation.
- **Probe/evidence:** the selected rule compares exact room-relative coordinates. The shifted-same-shape branch makes translation normalization wrong; the witness fired 289/600 times and all 60 checked rival claims disagreed.
- **Failure mode prevented:** matching only translation-normalized motif shape.
- **Limitation:** rotations/reflections are not a separate axis because the authority does not normalize them.

### `room_h = 3..5`

- **Original state/rationale:** the old declared and difficulty-specific ranges disagreed, causing rejected legal overrides.
- **Decision:** one full valid domain in every band. Easy/hard retain boundary-skewed defaults; medium samples uniformly to cover canonical 7/9-row profiles.
- **Alternatives considered:** difficulty-narrowed domains; uniform sampling in every band.
- **Probe/evidence:** a pinned regression first failed because medium had zero profile hits. Uniform medium height produced final cross-band support and 11/60 exact profiles.
- **Failure mode prevented:** declared override rejection and a medium-band profile hole.
- **Limitation:** canonical room height 6 is accepted by `strict_canonical_like` but not ordinarily generated.

### `room_w = 4..6`

- **Original state/rationale:** old width/column combinations could exceed 30.
- **Decision:** generate 4..6 while accepting canonical widths through 7.
- **Alternatives considered:** generate 7-wide rooms; reduce the number of row-layout rooms.
- **Probe/evidence:** four 7-wide rooms plus five walls produce width 33. Limiting generated width to 6 gives a maximum row width of 29 and preserves all four mapping rooms.
- **Failure mode prevented:** illegal 33-wide inputs and OOB outputs.
- **Limitation:** the exact 7x33 canonical test profile is accepted but not generated.

### `motif_size = 3..5`

- **Original state/rationale:** motif complexity was not a clean observable contract.
- **Decision:** use connected motifs of three to five cells, equal size within one input.
- **Alternatives considered:** singleton/two-cell motifs; larger motifs.
- **Probe/evidence:** canonical motifs have sizes 3 or 4. Three to five cells remain readable, fit the smallest room, and support multiple legal translations.
- **Failure mode prevented:** trivial one-cell color markers and motifs that cannot shift.
- **Limitation:** larger or disconnected motifs are not explored.

### Motif bank and placement

- **Original state/rationale:** unknown beyond ad hoc sampling.
- **Decision:** use a small connected shape bank whose members fit the minimum room and, for the shifted branch, have at least two legal translations.
- **Alternatives considered:** rejection-sample arbitrary cell sets; enumerate all polyominoes.
- **Probe/evidence:** deterministic bank selection avoids unbounded retries and every override combination passed 12,870 contract draws.
- **Failure mode prevented:** disconnected noise, impossible placements, and nondeterministic retry behavior.
- **Limitation:** the finite bank is not exhaustive.

### Colors

- **Original state/rationale:** canonical wall/motif/fill conventions were already stable; palette axes and texture aliases were dead or misleading.
- **Decision:** generate wall `1`, motif `6`, query background `0`, and two distinct fills from `(2,3,4,5,8)`. Accept wall colors `1/7/9` when parsing canonical-like inputs.
- **Alternatives considered:** expose palette/wall axes; retain `palette_kind`, `palette_size`, and textures.
- **Probe/evidence:** old helpful textures were byte-identical to default and negative fixtures contaminated the valid domain. Removing them produced zero linter warnings and zero override findings.
- **Failure mode prevented:** silent no-op overrides and conflating semantic variation with decorative recoloring.
- **Limitation:** ordinary color generalization is narrower than structural generalization.

### Eight-profile schedule

- **Original state/rationale:** sampling was independent and provided no lesson-level guarantee.
- **Decision:** index an eight-row orthogonal teaching table by `sample_index % 8`; every four consecutive profiles contain both values of all four semantic axes.
- **Alternatives considered:** pure random choices; hand-special-case only canonical profiles.
- **Probe/evidence:** all 12 four-demo lessons passed `lesson_identifiable`; profile coverage was nonzero for all eight profiles in each difficulty band.
- **Failure mode prevented:** unlucky lessons in which a reading-order or spatial rival survives every demonstration.
- **Limitation:** the schedule is deliberate rather than IID; consumers should preserve sample indices when assembling lessons.

### Keyed RNG and override provenance

- **Original state/rationale:** defaults and overrides bypassed one another, exact axes lacked provenance, and unknown keys were swallowed by `**overrides`.
- **Decision:** every axis uses `gen_ctx`; scheduled choices still execute a full-domain keyed draw; unknown names are rejected before generation.
- **Alternatives considered:** directly assign schedule values without a draw; retain legacy permissive keys.
- **Probe/evidence:** final override gate accepted 12,870/12,870 draws across 143 cases and three bands, with unknown-key verdict `rejected`.
- **Failure mode prevented:** typoed axes reading as successful, non-replayable defaults, and untestable accepted overrides.
- **Limitation:** `_scheduled_choice` is intentionally specialized to preserve both schedule determinism and provenance.

### Self-check, observer, and Python output mirror

- **Original state/rationale:** the old check was too permissive and no observer existed.
- **Decision:** parse connected non-wall rooms, validate exact role/motif/fill invariants, recover every axis, and independently solve the input in Python.
- **Alternatives considered:** validate only dimensions/colors; rely entirely on Racket smoke.
- **Probe/evidence:** all canonical inputs pass; all 60 ordinary checks pass; 45/45 destructive mutations fail; Python output equals every canonical output.
- **Failure mode prevented:** malformed rooms, unmatched motifs, duplicate fills, fake overrides, and Racket-only blind spots.
- **Limitation:** parser classification assumes majority-filled examples and motif-only queries, matching the authority's intended manifold.

### Semantic rivals and witnesses

- **Original state/rationale:** none were declared.
- **Decision:** make same order, reverse order, nearest example, and offset-ignoring shape matching executable; declare witnesses and a lesson-level survivor check.
- **Alternatives considered:** prose-only review notes; rely on generic diversity metrics.
- **Probe/evidence:** 5/5 witness types fired, 5/5 rival claims were verified, and 12/12 lessons were identifiable.
- **Failure mode prevented:** high visual diversity masking a semantically shortcuttable curriculum.
- **Limitation:** new plausible rivals should be added explicitly as they are discovered.

### Racket rule unchanged

- **Original state/rationale:** selected authority already matched canonical outputs.
- **Decision:** repair distribution/contracts only.
- **Alternatives considered:** style-only rewrite or a new implementation.
- **Probe/evidence:** authority synchronization and execution parity pass; 120/120 generated calls succeed.
- **Failure mode prevented:** unnecessary authority drift.
- **Limitation:** three nonblocking style findings remain in canonical Racket source.
