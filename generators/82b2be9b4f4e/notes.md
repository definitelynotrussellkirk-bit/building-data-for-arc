# Working notes: 82b2be9b4f4e

## Review review-50a65f644b693fed

Baseline generator SHA-256:
`38bcfbfa5b250479de3e7d98ce6f38d1da53e0ef1a0b662c912c74ef4ed5111d`.
Final generator SHA-256:
`31fbbaca003a4ae974746c74ae007a02fa6dbef7ef9592f13c5b3a159ac8fd8a`.
The canonical Racket authority was not changed.

### Root causes found

- The generator had no `RULE_HASH`, advertised several controls that were dead
  or misleading, accepted unknown overrides, and used difficulty-local draw
  bounds that contradicted the published axis domain.
- Retry placement could silently underfill/merge requested object roles, while
  `self_check` accepted structural impostors.
- It had no executable semantic contract for the canonical-fitting
  `merge_all_matching_pixels` shortcut.
- An initial repaired sampler covered winner sizes 3–5 but missed canonical
  winner size 7.
- An initial three-slot lesson schedule could put the only discriminator in the
  query. The retained red test failed at `('easy', 0, 0, 1)`.

### Repair

- Replaced the body with a constructive, backtracking object placer. Requested
  roles are either all placed or generation fails loudly; object candidates are
  cached as immutable templates for fast exhaustive override checks.
- Reduced the public contract to five controls that are exact and observable in
  every difficulty band. Unknown keys, invalid values, and invalid difficulties
  now fail immediately.
- Added canonical component-size support, including a compact seven-cell C
  polyomino, plus canonical/discriminator/broad profiles.
- Added strict structural analysis, `observe_overrides`, canonical acceptance,
  semantic witnesses/rivals, and the pinned rule hash.
- Adopted the four-slot schedule
  `canonical, discriminator, broad, discriminator`; any three of four
  consecutive pairs retain at least one two-key-object witness.
- Added 23 task-local regressions and the reusable cyclic rotation probe in
  `workspace/lesson_rotation_probe.py`.

### Final measured evidence

- Full battery: 12/12 green.
- Task-local tests: 23/23 passed.
- Override matrix: 30,870/30,870 accepted draws, 343 cases, three bands,
  zero findings or undeclared rejections.
- Semantic gate: 600/600 strict-valid, 5/5 canonical accepted, declared rival
  verified, witness fired 380/600.
- Profile floor: 12/60 exact canonical profiles and 22/60 canonical-envelope
  profiles, with every band passing.
- Source-bound lesson census: 300/300 lessons materialized, 1,200 unique inputs,
  zero survival of the declared rival.
- Cyclic rotation probe: 4,800 rotated lessons over 1,200 windows, zero rival
  survival, and at least one witness in every three-demo set.

Finite declared-rival tests do not prove universal identifiability. The sampler
also intentionally stays on a separated-object, pure-winner-bbox manifold; that
is a documented distribution choice rather than a claim that it exhausts every
input accepted by the authority.
## Current reviewer considerations

Source SHA-256: `31fbbaca003a4ae974746c74ae007a02fa6dbef7ef9592f13c5b3a159ac8fd8a`.

# Design decisions: 82b2be9b4f4e

## D1 — Keep the canonical Racket authority unchanged

**Choice.** Pin `RULE_HASH = "eff131529ace"` and repair only the input sampler,
validation, tests, and task-local review tooling.

**Reason.** Rule smoke and all canonical pairs showed that the selected authority
already implements the intended transformation: clear the bottom-left key,
select the largest connected object of that color, crop its input bounding box,
and scale by 2. The failures were in the generated distribution and its contract,
not in the authority.

**Alternative rejected.** Editing Racket to fit the old sampler. That would have
changed a correct label authority to accommodate bad data.

## D2 — Publish only five exact, observable axes

**Choice.** Keep `grid_h`, `grid_w`, `key_color`, `n_key_blobs`, and
`n_distractors`, with one global valid domain for every difficulty band.

**Reason.** Each value is directly recoverable from a valid grid and can be
round-tripped by `observe_overrides`. This makes the override API falsifiable.
Difficulty changes default weighting, not which declared values are legal.

**Alternatives rejected.** Retaining decorative palette/texture/position axes or
silently ignoring unknown keys. Those options made different requests return the
same object and hid caller mistakes. Declaring band-specific incompatibilities
was also rejected because every combination of the five small domains is
constructively feasible.

**Probe.** `test_exact_axes_round_trip_in_every_band`, the invalid/unknown override
tests, and the 30,870-draw framework override matrix.

## D3 — Construct all roles or fail loudly

**Choice.** Represent the winner, optional keyed loser, and each distractor as an
explicit role, then place all roles with bounded backtracking and orthogonal
halos. Protect the winner's entire bounding box from other objects.

**Reason.** The old retry loop could silently skip a requested object or permit
same-color fragments to merge, so requested counts were not trustworthy.
Constructive placement makes the returned grid the exact requested scene.

**Alternative rejected.** More random retries plus a fallback single pixel. That
would still bias the distribution and conceal infeasible branches. Minimum-canvas
stress tests show the selected domains are feasible without dropping roles.

**Performance choice.** Cache immutable candidate-placement tuples by
shape/height/width, copy only the candidate list before shuffling, and leave the
cache unmodified. This preserves determinism while making exhaustive checks fast.

## D4 — Cover canonical profiles without cloning only canonical examples

**Choice.** Use canonical, discriminator, and broad profiles. Canonical slots use
small dimensions and one keyed object; broad slots cover the full size/count
surface; discriminator slots force two keyed objects of distinct sizes. Include
winner shapes whose component sizes cover canonical sizes 4 and 7.

**Reason.** The first rewrite was lawful but its generated winner sizes were
`{3,4,5}`, missing canonical size 7. Adding the seven-cell C shape closes that
support hole while preserving nonrectangular outputs and broad shape diversity.

**Alternative rejected.** Hard-coding canonical grids or only canonical
shapes/dimensions. That would pass profile gates while reducing data diversity.

**Probe.** The retained red size test, final profile floor, and diversity stage.

## D5 — Use two discriminator slots in every four-pair cycle

**Choice.** `SCHEDULE_PROFILES = ("canonical", "discriminator", "broad",
"discriminator")`.

**Reason.** The earlier three-slot cycle had one discriminator. When that pair was
held out as the query, all three demos could remain consistent with the
canonical-fitting `merge_all_matching_pixels` shortcut. The retained red test
reproduces this at `('easy', 0, 0, 1)`. With two discriminator positions, deleting
any one of four pairs leaves at least one witness among the three demos.

**Alternatives rejected.** Relying on pooled witness frequency, or putting a
single discriminator in every three examples. Neither controls which example is
the query. Making all four slots adversarial was unnecessary and would discard
canonical-like coverage.

**Probe.** `workspace/lesson_rotation_probe.py` checks all four query choices for
100 seeds × 4 starts × 3 bands: 4,800 lessons, zero rival survival.

## D6 — Make the semantic claim executable

**Choice.** Declare the rival `merge_all_matching_pixels`, the witness
`multiple_matching_objects`, their mapping, and the same rival in both
`CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`.

**Reason.** The shortcut fits all five canonical pairs, so mere canonical parity
cannot show that generated lessons teach “largest connected component.” A scene
with two differently sized keyed components separates the two rules directly.

**Alternative rejected.** A prose-only warning or a witness count with no full
lesson check. A learner sees demos, not pooled marginals, so the complete lesson
must refute the rival.

## D7 — Strict validation matches the documented manifold

**Choice.** Validate dimensions/colors, isolated bottom-left key, one or two
keyed components with unique sizes, two or three one-component distractor colors,
object separation, winner-bbox purity, and winner nonrectangularity. Check exact
overrides when metadata is supplied.

**Reason.** `self_check` should reject impostors rather than merely confirm that
some nonzero cells exist. The same analysis powers `strict_canonical_like` and
`observe_overrides`, reducing inconsistent interpretations.

**Limitation.** The authority itself can process some grids outside this strict
separated-object manifold. This generator deliberately does not claim exhaustive
task-domain coverage; any future broadening should add corresponding semantic
competitors and tests.
