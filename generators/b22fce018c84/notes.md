# Working notes: b22fce018c84

## Current rule and authority

The unchanged selected Racket rule (normalized hash `149529c7164c`) preserves every
orange (`7`) source and adds its reflection across the horizontal midline at
`(h - 1 - r, c)`. Generator version `2.0.0`, final source SHA-256
`361a31e3eab356f2c4d319fe2573f090cac19dab61b32a08c5bbc3ec949c8736`, is pinned
to that rule. No Racket source was edited.

## Prior state and lead used

The selected baseline was version `1.2.1`, SHA-256
`1f22e662156be75fe2c3b622946940a7fff3440cf8bf0b4afc55de9599ae489a`.
It advertised nine controls but ignored or contradicted many of them, accepted unknown
keys, exposed validator-failing negative textures as ordinary axis values, had no
`RULE_HASH`, and had no executable lesson-rival contract. I used the unresolved audit
from `review-bd22d04aaf51157f:v0001` as a lead: its easy/seed-15154 lesson put every
source on the center column, so horizontal reflection and 180-degree rotation were
indistinguishable in all demonstrations.

## Current design decisions

- Public controls are only `grid_h=7..14`, `grid_w=7..14`, `n_markers=2..8`, and
  `position_bias=top_half|bottom_half|mixed`. Every combination is feasible, exact,
  and recoverable by `observe_overrides`; unknown, mistyped, and out-of-range values
  reject loudly.
- A four-position cyclic schedule provides: a strict canonical top-only profile, a
  top same-row adjacency, a bottom same-column adjacency, and a mixed profile carrying
  both adjacency directions. Every four-pair lesson therefore contains the four
  profiles, and every three-demonstration query rotation retains witnesses against
  each declared competitor.
- The broad input grammar permits top, bottom, and mixed sources but excludes centerline
  sources and pre-completed mirror pairs, since those hide an observable completion.
  Bare four-cell lines and bare solid 2x2 blocks are also excluded: they are not used by
  this teaching curriculum and triggered the generic minimal-impostor detector.
- The strict canonical profile uses the five published shapes, three or four top-half
  markers, distinct rows, distinct columns, and no orthogonal adjacency. Its scheduled
  rate is 1/4, above `MIN_STRICT_FRAC=0.20`.
- The executable competitor set is: identity, 180-degree addition, vertical addition,
  top-only, bottom-only, isolated-only, first-per-row, first-per-column, and first-three.
  `top_only`, `isolated_only`, `first_per_row`, and `first_per_column` are explicitly
  checked as shortcuts that fit every canonical pair.

## Reversals and failed iterations retained

1. The first repair accepted bare four-cell lines and solid 2x2 blocks. The first full
   after battery passed 11 stages but failed `defect_lint`; a new regression failed
   before the validator was narrowed. Evidence is under `checks/intermediate-defect-lint/`,
   `checks/tdd-red-minimal-impostors.log`, and
   `checks/tdd-green-minimal-impostors.log`.
2. The first mixed-profile implementation discarded all reserved anchors when one
   randomly chosen top/bottom mirror orbit collided. A 300-lesson census found one
   production ambiguity and five query-rotation ambiguities for `first_per_column`.
   Five exact seeds were added as failing regressions. The anchor chooser now enumerates
   collision-free placements before sampling one. The failed and passing censuses are
   retained compressed under `checks/lesson-census-final*.json.gz`.

## Final evidence and limits

The final official battery is 12/12 green; portable focused tests are 67/67. The exact
override matrix accepted 24,660/24,660 draws across 274 cases and three bands with zero
findings or warnings. A random production census materialized 300 lessons / 1,200 pairs
and checked 1,200 query rotations with zero declared-rival ambiguities; fixed-seed
schedule enumeration covered 12 lessons and 48 rotations with zero ambiguities.

These are finite checks against declared rivals, not a proof of unique induction against
all possible programs. Supported teaching inputs are 7..14 square or rectangular grids,
2..8 orange sources, no odd-height centerline source, no already-completed horizontal
mirror pair, and no bare four-cell-line or solid-2x2 endpoint. The hand-authored lawful
bottom-source counterexample in `counterexamples/top-only-bottom-source.json` refutes the
strongest canonical shortcut.
## Current reviewer considerations

Source SHA-256: `361a31e3eab356f2c4d319fe2573f090cac19dab61b32a08c5bbc3ec949c8736`.

# Decisions for b22fce018c84

## D1 — Keep the Racket authority unchanged

**Original state.** The selected rule already matches all canonical pairs and has clear,
general semantics: add every source's horizontal reflection.

**Decision.** Pin normalized rule hash `149529c7164c`; change only generator-side files.

**Alternatives rejected.** Restricting the rule to top-half sources would preserve the
published examples but encode their accidental sampling bias. Rewriting equivalent
Racket would create needless authority-divergence risk.

**Probe.** Final `rule_smoke`, `racket_lint`, and `authority_sync` stages are green.

## D2 — Replace the nine-axis surface with four exact observable controls

**Original state.** The old surface mixed real dimensions with dead palette/count aliases,
contradictory texture endpoints, and unvalidated unknown keys. Its partial baseline
override stage reported 22,409 findings and 62,160 undeclared rejections.

**Decision.** Expose only `grid_h`, `grid_w`, `n_markers`, and `position_bias`. Validate
before constructing `gen_ctx`, record each exact draw, and recover each value from the
grid through `observe_overrides`.

**Alternatives rejected.** Keeping compatibility aliases would preserve a misleading API;
marking broad combinations incompatible would make a small, fully feasible geometry look
more complex than it is.

**Probe.** Final override evidence covers 274 cases × 30 seeds × 3 bands = 24,660 accepted
draws, with zero findings, zero warnings, and strict unknown-key rejection.

## D3 — Teach the source domain, not the canonical top-only accident

**Original state.** Every canonical source is above the midline. The prior audit also
found a complete lesson where all markers lay on the center column, letting 180-degree
rotation survive all demonstrations.

**Decision.** Use a cyclic four-profile schedule: canonical top, top same-row adjacency,
bottom same-column adjacency, and mixed dual adjacency. The schedule has period four and
three demonstrations plus one query.

**Alternatives rejected.** Pure random placement can have good marginal witness frequency
while still producing a bad complete lesson. Increasing the demonstration count would
mask rather than fix the schedule.

**Probe.** The final random census checks 300 production lessons and all 1,200 query
rotations; fixed-seed enumeration checks all four starts in all three bands and all 48
rotations. Both report zero ambiguity against the declared rivals.

## D4 — Make the mixed witness construction collision-proof

**Failed first choice.** The first implementation sampled one top pair and one bottom pair;
if any horizontal-mirror orbit collided, it discarded the whole anchor set and filled the
scene randomly.

**Evidence.** The intermediate census found 1/300 production lessons and 5/1,200 rotations
ambiguous for `first_per_column`. Five exact source-bound seeds failed the new regression.

**Reversal.** Enumerate all collision-free bottom-pair placements compatible with the
chosen top pair, then sample from that nonempty list. This guarantees both same-row and
same-column witnesses for every default mixed profile.

**Failure mode retained.** The failed census and red test log remain in `checks/`.

## D5 — Narrow two generic minimal impostors

**Failed first choice.** A broad validator accepted an isolated bare four-cell horizontal
line and bare solid 2x2 block. The rule is mathematically defined there, but these shapes
are not part of the selected teaching grammar and the strict defect policy treats their
acceptance as unadjudicated minimal impostors.

**Decision.** Reject only those two exact four-cell endpoints and make generation reroll
if an explicit override happens to form one. Adjacent evidence remains present in richer
five- and six-source profiles.

**Alternative rejected.** A free-form task-local waiver would leave the official battery
red and would not improve the explicit grammar.

## D6 — Domain limits

The generator deliberately does not teach centerline identity cases, already-completed
mirror pairs, grids outside 7..14 per dimension, more than eight sources, non-orange
colors, or the two excluded four-cell endpoints. Declared-rival checks are finite and do
not establish uniqueness against every conceivable program.
