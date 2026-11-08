# Working notes: bb41378fe3c8

## Current rule and authority

The selected Racket rule is unchanged and remains authoritative (`RULE_HASH =
 d655d37ca499`). Each input colour-2 cell is preserved and casts colour 5 into
its one-cell down-right neighbour **only** when that destination is in bounds
and is input background 0. A nonzero destination blocks the shadow; non-2 cells
are inert and preserved.

## Repair decisions (version 3.0.0)

1. **Exact construction replaced bounded rejection sampling.** Version 2.1.1
   could stop before satisfying `n_markers`; the retained seed-1 call requested
   seven markers on 6×6 and returned five. Version 3.0.0 constructs an exact
   separated marker set and observes every advertised axis. The final source
   returns seven markers for all seeds 0–199 in that historical sweep; focused
   tests also exercise the hardest Cartesian override in every difficulty band.
2. **Blocked destinations are intentional, not accidental.** The old prose said
   decoys never occupied marker destinations although generated examples could
   do exactly that. The new `marker_profile` axis explicitly distinguishes
   `plain`, `blocked`, `boundary`, and `mixed`. At most one blocker is generated,
   and `self_check` verifies it.
3. **Inert non-2 decoys are separately observable.** `n_decoys` counts only
   free non-2 cells, excluding the blocker. Each free decoy has an in-bounds
   background down-right cell, creating a clean counterexample to the plausible
   but wrong “every nonzero cell casts” rule.
4. **The public axis surface was narrowed.** Dead aliases (`palette_kind`,
   `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and
   `texture`) were removed. The remaining exact controls are `grid_h`, `grid_w`,
   `n_markers`, `marker_profile`, and `n_decoys`; unknown, mistyped, and
   out-of-range overrides fail loudly.
5. **Validation became structural.** `self_check` now checks ARC cell types,
   dimensions, output-only colour 5, marker count and separation, blocker and
   boundary cardinality, decoy semantics, and the existence of a visible shadow.
   Canonical inputs remain accepted. Task-local mutation fixtures and tests
   exercise destructive near misses.
6. **The lesson schedule teaches both hidden branches.** The period-eight
   schedule alternates canonical-profile anchors with rich odd-indexed examples.
   Every four consecutive pairs contain two rich examples; after holding out any
   query, at least one demonstration still refutes both declared canonical-fitting
   rivals. `lesson_identifiable` returns reasons rather than a Boolean.
7. **Difficulty is layout-sensitive, not a complexity claim.** The semantic
   profile is schedule-controlled in every band; the optional difficulty label
   salts the keyed layout draw so bands are not byte-identical. It does not claim
   progressively harder rule induction.

## Evidence and retained leads

The repair used prior returns `review-08296b5f63a5e390:v0001` and
`review-47a0a3d8066b6da9:v0001` as leads. Both were bound to baseline generator
SHA-256 `cc1cb308bdcded56330f3f44382b48b2eef2ede485c3556e8a8e63fddc5753be`.
The first independently measured 117/200 exact-override underfills; the second
also identified the blocker/documentation mismatch and the canonical-fitting
`overwrite_blockers` shortcut.

Compact final reproducers are in
`counterexamples/repair-v3-regressions.json`. The reusable
`workspace/qualification_probe.py` iterates the generator's actual declared
rivals. On final source SHA-256
`c66198bf73390278aa2d3071415e09ad7e7157dd71d012f3d04b17b1886a39fd`, it reports:

- exact override: 200/200 seeds returned seven markers, 0 failures;
- declared shortcuts: both fit 3/3 canonical pairs;
- cyclic curriculum: 1,024/1,024 band/seed/start/query-position checks had no
  surviving declared rival.

The Racket-backed battery and 100-lessons-per-band census are retained separately
under the review's `checks/` directory; they remain the authority for generated
outputs.

## Known limits

- The rival set is finite. Passing it does not prove unique induction against
  every possible program.
- Constructed marker locations use a parity lattice to guarantee every legal
  joint override. Canonical inputs need only satisfy the broader separation
  grammar and are not restricted to that lattice.
- Input colours 2 and output colour 5 retain fixed semantic roles. This task is
  not colour-permutation invariant.
- Three demonstrations are assumed. Arbitrary shuffling outside the four-pair
  schedule can discard required witnesses; callers should preserve scheduled
  neighbourhoods or call `lesson_identifiable`.

No known blocker remains in the selected generator. Imported associated notes
retain original evidence and timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `c66198bf73390278aa2d3071415e09ad7e7157dd71d012f3d04b17b1886a39fd`.

# Decisions: bb41378fe3c8 repair

Final generator: version `3.0.0`, SHA-256
`c66198bf73390278aa2d3071415e09ad7e7157dd71d012f3d04b17b1886a39fd`.
The Racket rule was not changed; its normalized authority hash remains
`d655d37ca499`.

## D1 — Replace rejection sampling with exact construction

**Prior choice.** Version 2.1.1 repeatedly sampled candidate cells and stopped
when it ran out of attempts. Its public `n_markers` control therefore described
a target, not a guarantee. The retained call `(seed=1, sample_index=0,
grid_h=6, grid_w=6, n_markers=7)` returned only five markers, and the prior
review measured 117 underfills in 200 seeds.

**New choice.** Construct marker coordinates from a parity lattice with enough
capacity for every legal 6–11 grid / 3–7 marker combination, choose exactly the
requested count, then reserve target cells for the selected blocker/boundary
semantics before placing decoys.

**Why.** Exact overrides are part of the generator contract. A constructive
method makes the guarantee evident, deterministic, and cheap to verify.

**Rejected alternatives.** Increasing the retry budget still leaves a
probabilistic contract. Silently clipping `n_markers` to available capacity would
repeat the original dishonesty. Declaring many incompatibilities was unnecessary
because the complete advertised Cartesian product is realizable.

**Probe/failure modes.** The reusable probe sweeps seeds 0–199 for the historical
hard call; task tests cover the hardest Cartesian combination in every band.
The shared override stage covers 24,840 draws. Remaining restriction: generated
markers lie on a parity lattice, although `self_check` intentionally accepts the
broader canonical separation grammar.

## D2 — Narrow the public axis surface

**Prior choice.** The baseline advertised broad marker ranges and aliases such as
`palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`,
and `texture`; several were ignored, overlapping, or admitted degenerate values.

**New choice.** Keep only five independently observable controls:
`grid_h`, `grid_w`, `n_markers`, `marker_profile`, and `n_decoys`. Validate unknown
keys, exact Python integer types (rejecting booleans), ranges, and enum values
before generation.

**Why.** A small exact contract is more useful than a large aspirational one and
allows exhaustive matrix testing.

**Rejected alternatives.** Keeping aliases for compatibility would preserve two
names for one latent variable and make exact observation ambiguous. Retaining a
`texture` axis for invalid fixtures would mix ordinary generation with negative
tests; malformed/degenerate cases belong in test fixtures.

**Failure modes/limits.** Color roles remain fixed: marker 2, shadow 5, background
0. This task is not color-permutation invariant, and no palette axis is claimed.

## D3 — Make blockers, boundaries, and decoys intentional

**Prior choice.** A random decoy could land on a marker's destination even though
notes said destinations were empty. The resulting example accidentally exercised
a real rule branch without describing or counting it.

**New choice.** `marker_profile` explicitly selects `plain`, `blocked`,
`boundary`, or `mixed`. A blocker is a nonzero cell at one in-bounds marker
destination; an inert decoy is counted separately and must itself have an
in-bounds background down-right cell. At most one blocker and one clipped marker
are generated.

**Why.** These are semantic branches, not cosmetic noise. Separate observability
lets tests and lesson checks distinguish them.

**Rejected alternatives.** Forbidding blockers would make the canonical-fitting
“overwrite every destination” shortcut permanent. Treating the blocker as one
of `n_decoys` would make that axis semantically ambiguous. Adding many blockers
would overemphasize the exception relative to the simple core operation.

**Probe/failure modes.** The retained JSON contains exact blocker and inert-decoy
witnesses with intended and rival outputs. `self_check` verifies both. A finite
witness set does not prove uniqueness against every conceivable program.

## D4 — Use a period-eight, rotation-safe teaching schedule

**Prior choice.** Independently random examples could produce three demonstrations
that all fit both plausible rivals, even if witness cases appeared elsewhere in
the overall distribution.

**New choice.** Alternate canonical-size/palette anchors at even indices with rich
odd-indexed examples. Any four consecutive pairs contain two rich examples;
with any single pair used as query, at least one rich demonstration remains.
`EXAMPLES_NEEDED = 3`, and `lesson_identifiable` returns named reasons when a
lesson fails the declared-rival policy.

**Why.** Lesson-level identifiability, not marginal witness frequency, is the
relevant training property. The schedule also guarantees canonical-profile
support in every band.

**Rejected alternatives.** Pure rejection/resampling at lesson assembly would be
harder to replay and could bias sample indices invisibly. Putting a witness in
every pair would reduce distribution diversity and make the task stylistically
formulaic. Four or more demonstrations were unnecessary once the schedule
provided two rich slots per window.

**Probe/failure modes.** The source-bound census checks 100 lessons per band and
all four held-out query positions. `qualification_probe.py` additionally checks
all eight cyclic starts, four query positions, eight seeds, and four band labels.
Arbitrary shuffling of unrelated pairs is not promised; callers should preserve
scheduled neighborhoods or invoke `lesson_identifiable`.

## D5 — Strengthen `self_check` structurally without encoding the constructor

**Prior choice.** The validator accepted every one of 62 generic destructive
mutations and several degenerate textures.

**New choice.** Validate the semantic input domain: ARC cell types, rectangular
shape and dimensions, palette roles, 3–7 markers, Chebyshev separation, bounded
blocker/boundary counts, decoy semantics, and at least one visible shadow. Keep
construction-specific parity out of validation.

**Why.** A validator should characterize lawful task inputs rather than simply
rubber-stamp generator output or demand one implementation's layout.

**Rejected alternatives.** Comparing against generation metadata would not work
for canonical or externally authored inputs. Requiring parity coordinates would
reject valid canonical examples. Requiring every marker to cast would erase the
blocker and boundary branches.

**Probe/failure modes.** All three canonical inputs pass. The generic gate rejects
31/60 destructive mutations; the focused suite additionally rejects every
malformed and task-specific structural fixture. Some generic mutations preserve
a lawful scene, so 60/60 generic rejection is neither expected nor desirable.

## D6 — Let difficulty affect layout, not claim semantic progression

**Intermediate failure.** After the main repair, the defect linter found that
easy/medium/hard produced byte-identical layouts for the same keyed call.

**New choice.** Salt only the keyed layout RNG with the difficulty label while
using the same semantic schedule in all bands.

**Why.** The label now has observable effect and avoids duplicate corpora, but the
code does not make an unsupported claim that this one-operation task has a
meaningful easy-to-hard induction ladder.

**Rejected alternative.** Escalating marker count or hiding branch witnesses by
band could make easy lessons ambiguous or change the semantic support policy.

## D7 — Preserve the canonical Racket authority

The observed defects were all in generation, validation, or lesson assembly.
The selected Racket rule already matched all canonical outputs and states the
intended conditional write correctly, so changing it would add risk without
repairing any identified problem. `RULE_HASH = "d655d37ca499"` now pins that
authority, `rule_mirror` is independently tested, and final authority sync passed.

## D8 — Retain compact future-agent tooling and evidence

Added:

- `repo/generators/bb41378fe3c8/workspace/qualification_probe.py`, which derives
  rival names from the generator declarations, verifies they fit every canonical
  pair, sweeps the historical exact override, and enumerates cyclic lesson starts;
- `repo/generators/bb41378fe3c8/counterexamples/repair-v3-regressions.json`, which
  stores the smallest useful historical and semantic witnesses;
- focused tests under the selected task's `tests/` directory.

These are task-local because their rival semantics and schedule are task-specific.
The larger Racket-backed battery and lesson census remain authoritative for
outputs; the compact probe explicitly labels its generated labels as mirror-based.

## Prior evidence used as leads

I used `review-08296b5f63a5e390:v0001` for the underfill reproducer and
`review-47a0a3d8066b6da9:v0001` for the blocker/documentation mismatch and
`overwrite_blockers` rival. Both were tied to baseline generator SHA-256
`cc1cb308bdcded56330f3f44382b48b2eef2ede485c3556e8a8e63fddc5753be`.
I re-measured the current baseline and final source rather than treating prior
claims as present-source results.
