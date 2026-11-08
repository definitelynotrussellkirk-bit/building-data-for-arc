# Working notes: 38300735cc4d

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-09-28 review: blocker-frequency shortcut

- Baseline version `3.0.0` passed all 12 battery stages but coupled every blocker to a color occurring exactly once.
- The branch-specific rival `block_only_singletons` therefore fit both canonical demonstrations and every old generated blocker example.
- Version `3.1.0` adds a second independently blocked pair to `blocked` and `mixed`: its blocker color occurs three times, with two noncollinear markers outside all reserved semantic spans.
- Every blocker-bearing sample now has blocker color counts `[1, 3]`, refuting both singleton-only and repeated-only obstruction rules.
- The repeated blocker deliberately uses count three rather than two so it cannot become an eligible endpoint pair.
- The canonical Racket authority was not changed; rule hash remains `e1f30dfc7d44`.
- Focused regression: `test_blocker_profiles_refute_blocker_count_shortcuts` failed before the implementation and passes afterward for both blocker-bearing profiles.
- Evidence: `checks/38300735cc4d_counterexample.json`, before/after battery summaries, and post-change semantic-gate report.
- Remaining boundary: counts above three are not enumerated; the curriculum uses the smallest repeated ineligible count needed to separate global-frequency behavior.
## Current reviewer considerations

Source SHA-256: `a480b37973c7a23292633507fa894c5aa6d4efb89c4ab6e4ed71bb0f4394f019`.

# Design decisions: 38300735cc4d

## Rule authority

**Choice.** Keep the existing Racket rule unchanged: for each nonzero color occurring exactly twice, bridge the inclusive row or column segment only when the strict interior is all zero.

**Rationale.** The source rule, written solution, Python mirror, rule-smoke checks, and authority-sync checks already agreed. The discovered problem was distributional, not an authority defect.

**Alternative rejected.** Encoding blocker-frequency logic in the Racket rule would have made the authority less general and would contradict the written task.

**Probe.** Before and after batteries both passed rule smoke and authority synchronization; the exact counterexample has `racket_equals_mirror: true`.

## Grid dimensions

**Choice.** Retain the observable `grid_h` and `grid_w` axes over `6..12`; canonical-scale profiles remain square with side `9..11`.

**Original rationale.** The canonical examples are 9–11 cells per side, while the wider range gives enough layout room for independent semantic branches.

**Alternatives.** Smaller grids increase placement failures and force semantic spans to interact. Much larger grids dilute the sparse ARC morphology and make shortcut examples less salient.

**Probe.** The profile-floor gate found canonical support in every difficulty band; the override contract accepted all valid dimension cases and rejected invalid ones.

**Limitation.** Most strict canonical-like examples remain square, so rectangularity is taught mainly outside the strict subset.

## Six-profile schedule

**Choice.** Keep the deterministic six-profile cycle:

1. `canonical_long`
2. `blocked`
3. `count_decoy`
4. `clean_varied`
5. `alignment_decoy`
6. `mixed`

**Original rationale.** Each profile isolates one semantic branch, while a rolling window of five examples must eliminate identity, one-orientation, blocker-ignorant, wrong-count, and nonalignment rivals.

**Alternative rejected.** Pure random mixtures can produce short lessons that omit a critical branch. A larger fixed cycle would increase the minimum demonstration count.

**Probe.** Twelve generated five-demo lessons were all identifiable after the change, with no surviving declared competitor.

## Endpoint-pair geometry

**Choice.** Use two disjoint pair segments for clean/count/alignment profiles and three for blocker-bearing profiles. Every lawful sample includes at least one horizontal and one vertical pair.

**Rationale.** Disjoint spans make causal differences legible and prevent one role from overwriting another. Three spans are required to carry two distinct blocked paths while retaining a clear bridge.

**Alternatives.** Reusing one blocked path for both blocker frequencies is impossible in one grid. Allowing crossing spans makes blocker membership ambiguous and complicates both validation and teaching.

**Probe.** `self_check` rejects intersecting paths, missing orientations, and profiles with the wrong number of blocked branches.

## Blocker-frequency curriculum

**Choice.** Every `blocked` and `mixed` scene has:

- one singleton-color blocker in one path interior;
- one color occurring three times, with exactly one occurrence in another path interior;
- separate colors for the two blockers;
- exactly one blocker cell per blocked path.

**Rationale.** The baseline covered obstruction but coupled it perfectly to global color count one. Counts `[1, 3]` directly refute both plausible frequency-conditioned rules.

**Why count three.** A blocker color occurring twice could itself be interpreted as a candidate endpoint pair. Three is the smallest repeated count that is unambiguously ineligible under the exact-count rule.

**Why noncollinear.** A collinear three-marker blocker could also instantiate the wrong-count/extrema branch. Noncollinearity keeps the new witness specific to blocker frequency.

**Why the extra markers avoid reserved spans.** Otherwise the repeated color could block more than one pair or corrupt a count/alignment decoy.

**Alternatives rejected.** One color blocking two paths confounds blocker membership. Four or more markers add density without strengthening the identified counterexample. A singleton-only curriculum preserves the bug.

**Probe.** The new test first failed with observed blocker counts `[1]`; after the change both profiles produce `[1, 3]`. The semantic gate recorded 177 hits for each new witness across all bands and 60/60 associated rival disagreements.

**Limitation.** The curriculum does not enumerate every frequency above three; it targets the minimal independent contrast.

## Wrong-count decoy

**Choice.** Retain one color with exactly three collinear markers and an unfilled gap in `count_decoy` and `mixed`.

**Rationale.** This isolates the exact-count requirement against a rival that fills between extrema for any repeated color.

**Alternative rejected.** Two markers would be a lawful pair; four markers add no new decision boundary for the current rule.

**Probe.** `exactly_two_markers_required` fires in all bands and refutes `fill_extrema_any_count`.

## Nonalignment decoy

**Choice.** Retain one two-marker color whose cells differ in both row and column in `alignment_decoy` and `mixed`.

**Rationale.** This isolates row/column alignment without changing the color-count condition.

**Alternative rejected.** A diagonal line or bounding-box object with more markers would also change the exact-count branch.

**Probe.** `row_or_column_alignment_required` refutes the branch-isolated `fill_bbox_for_two` rival.

## Palette and role separation

**Choice.** Keep background color zero privileged and assign distinct nonzero colors to every semantic role. Canonical-like scenes draw from the canonical foreground palette when possible.

**Rationale.** Role reuse can change global counts, accidentally form pairs, or make a blocker share endpoint semantics. Distinct colors make each branch independently observable.

**Alternative rejected.** Arbitrary movement of color zero is not a lawful palette permutation because zero controls both background and obstruction.

**Probe.** `self_check` validates role counts and rejects unsupported or isolated singleton colors.

## Difficulty

**Choice.** Difficulty changes size/span pressure but not the required semantic branches.

**Rationale.** A hard example should not silently omit a rule condition. The semantic census therefore expects every witness in every band.

**Probe.** All eight witnesses fired in easy, medium, and hard; no band was missing support.

## Validation architecture

**Choice.** Represent plausible wrong rules as executable rivals and bind each witness to a branch-specific rival.

**Rationale.** Surface statistics cannot establish that a lesson distinguishes the intended rule. Executable rivals turn each teaching claim into a falsifiable output disagreement.

**Alternative rejected.** A single broad rival can be killed by the wrong branch and falsely suggest that a lesson is identifiable.

**Probe.** The semantic gate reports no weak witnesses, no surviving competitor, and no rival errors.
