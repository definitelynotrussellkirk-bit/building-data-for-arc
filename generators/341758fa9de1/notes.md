# Working notes: 341758fa9de1

The 2026-10-05 review replaced the imported v1.3.0 generator with a v2.1.0
curriculum-safe implementation. The selected Racket authority was not changed.

Key maintenance constraints:

- keep `RULE_HASH = "6e591d69c073"` synchronized with the selected authority;
- all advertised axes must remain exactly observable from returned pixels;
- every four-pair lesson (three demonstrations plus one query) must distinguish
  every declared competitor under every query rotation;
- retain public canonical size/palette anchors in every difficulty band; and
- rerun `workspace/probe_curriculum.py` whenever the schedule or rivals change.

Detailed rationale, rejected alternatives, and final evidence are in the review
return's `DECISIONS.md`, `REVIEW.md`, and `checks/` artifacts.
## Current reviewer considerations

Source SHA-256: `34e9545c482e4f2c32c6b5d7330bdde59a4c5ed173db9cee9593a43ffff9775c`.

# Decisions for 341758fa9de1

## Context and prior leads

I used no prior return as a lead. The selected baseline was inspected and tested
directly. Its original design rationale was not documented beyond a short task
summary, so where intent was unavailable I mark it as unknown rather than
retroactively attributing a reason.

## D1 — Keep the selected Racket authority unchanged

**Choice.** Preserve rule hash `6e591d69c073`: scan row-major, choose the first
nonzero color, keep every occurrence of that color, erase all others.

**Rationale.** An independent Python implementation reproduced every public
pair, and the live Racket smoke had no authority failure. The defects were in
the generator and curriculum, not the selected rule.

**Alternatives rejected.** Changing the rule to match a baseline generator
quirk would have broken canonical authority. Duplicating production labels in
Python was also rejected; `rule_mirror` is explicitly a review/test mirror.

**Probe and failure mode.** Final live smoke applied 120/120 inputs and compared
120/120 mirror outputs. A future rule change must update `RULE_HASH` and rerun
both authority synchronization and smoke evidence.

## D2 — Replace dishonest axes with five exact observable controls

**Choice.** Retain only `grid_h`, `grid_w`, `n_colors`, `palette_kind`, and
`key_frequency`. Unknown keys and invalid types/ranges fail closed.

**Original rationale.** Unknown. The baseline advertised controls such as fixed
single-token density/position choices and branches that did not reliably affect
pixels.

**Alternatives rejected.** Keeping legacy names as silent aliases would make the
API appear more expressive than the returned distribution. Marking them merely
diagnostic would preserve dead surface area without training value.

**Probe and limitations.** `observe_overrides` independently recovers all five
controls from pixels. The final matrix covers 515 cases, 30 seeds, and 3 bands
(46,350 draws). It proves exactness for the declared domains, not arbitrary
undeclared combinations.

## D3 — Use three disjoint palette families

**Choice.** `cool`, `warm`, and `varied` provide disjoint exact color sets for
3–5 nonzero colors.

**Rationale.** Exact sets make both palette family and color count observable
without hidden metadata. Literal ARC colors remain 0–9.

**Alternatives rejected.** Drawing arbitrary subsets would make a named palette
axis non-recoverable. A single palette would make the axis dead. Encoding the
key by a special fixed color would create a shortcut.

**Failure mode.** Palette identity can still correlate with other choices by
chance in finite samples; the schedule does not use palette to choose the key,
and the large census spans all declared competitors rather than claiming full
statistical independence.

## D4 — Anchor all public size/palette profiles

**Choice.** Sample-index residues 0–2 use the three public profiles
`(5,6,4)`, `(5,5,4)`, and `(5,6,5)` where the third value includes background;
residue 3 draws broader difficulty-weighted dimensions and 3–5 nonzero colors.

**Rationale.** The baseline produced no exact canonical profile in the measured
floor. Anchors keep generated training tied to public support while the fourth
slot supplies broader coverage.

**Alternatives rejected.** Pure random dimensions made small public profiles too
rare. Emitting only exact public shapes would overfit morphology and eliminate
useful extrapolation.

**Probe and limitation.** The profile floor found 52/60 exact hits and at least
one in every band. Shape/palette matching alone does not establish semantic
branch coverage; that motivates the answer in `QUESTION_ANSWER.md`.

## D5 — Make frequency rank a crossed teaching variable

**Choice.** Give every color a unique count and cycle the key through least,
middle, and most frequent. `key_frequency` remains an exact override.

**Rationale.** All public pairs are compatible with “choose most frequent,” so
a generator that usually repeats that pattern can teach the wrong rule even
with correct labels.

**Alternatives rejected.** Independent random counts can accidentally produce a
three-demo lesson in which one frequency rival fits every demonstration. Fixed
counts make frequency a permanent shortcut.

**Probe and failure mode.** Every four-pair window has at least two frequency
profiles after any single query is held out. The declared least/middle/most
rivals are checked directly; more elaborate count-based rules remain possible.

## D6 — Vary selector position and numeric palette rank

**Choice.** Use a period-4 numeric schedule `low, middle, high, middle` and four
selector-position slots. Position 0 deliberately includes `(0,1)`; the other
slots choose from disjoint feasible suffix buckets. Combined with the period-3
frequency schedule, the least common period is 12 and realizes every
frequency × numeric-rank combination.

**Rationale.** The first repair always put the selector at `(0,1)` and always
used an interior numeric color. Those were genuine newly introduced shortcuts,
found during the required final self-review.

**Alternatives rejected.** Merely documenting those restrictions would leave a
poor training curriculum. Fully random positions were also rejected because a
short lesson could accidentally repeat `(0,1)` and fail to refute the fixed-cell
rival.

**Probe and limitation.** New tests first failed with positions `{(0,1)}` and
missing numeric/fixed-position rivals, then passed after the change. Selector
positions are restricted to locations that leave enough row-major suffix cells
for exact counts and semantic witnesses; the schedule is broad, not uniform
over every cell.

## D7 — Reserve explicit semantic witnesses

**Choice.** Place a second key later in scan order, a different color at the
right edge of the selector's row, and a final decoy at bottom-right. Keep the
first key occurrence isolated from later key cells.

**Rationale.** This refutes “keep only the first component/cell,” “choose the
rightmost color in the first occupied row,” “choose the last color,” and
identity while keeping exact counts controllable.

**Alternatives rejected.** Hoping random placement would eventually produce
counterexamples is insufficient at lesson granularity. Hard-coding a complete
scene template would reduce diversity.

**Failure mode.** Reserved witness roles create some structured marginals. The
layout RNG still places the remaining exact counts freely in the feasible
suffix, and the final diversity probe measured 100% unique inputs over 300
pairs.

## D8 — Three demonstrations plus one rotation-safe query

**Choice.** `EXAMPLES_NEEDED = 3`; every sampled lesson contains four consecutive
schedule items, and any item may be the query. `lesson_identifiable` checks all
12 executable competitors.

**Rationale.** Three demonstrations are enough for the crossed period-3/period-4
schedule to show at least one counterexample to every fixed rank/position rival
after any one item is held out.

**Alternatives rejected.** Two demonstrations leave simple rivals underconstrained.
An ordered-only query policy was unnecessary once every rotation passed. More
demonstrations would increase token cost without being needed for the declared
hypothesis set.

**Probe and limitation.** The shared census checked 300 production lessons and
1,200 rotations; the local cyclic probe checked 288 overlapping windows and
1,152 rotations. Both iterate the generator's actual declarations. They do not
prove uniqueness against undeclared hypotheses.

## D9 — Separate broad validity from strict canonical likeness

**Choice.** `self_check` accepts rectangular 5–18 grids with 3–5 nonzero colors,
each occurring at least twice, and a repeated first key. `strict_canonical_like`
adds only the public shape/palette profiles.

**Rationale.** Conflating “lawful task input” with “exact public morphology”
would reject useful extrapolations or falsely label every broad draw canonical.

**Alternatives rejected.** A validator specialized to generated coordinates
would reject public inputs and hide support gaps. A no-op validator would admit
vacuous or malformed scenes.

**Probe and limitation.** All three public inputs are accepted; final semantic
strict rate is 471/600 (78.5%). Mutation sensitivity is intentionally partial:
48/60 destructive mutations were rejected, because some mutations remain lawful
instances rather than validator defects.

## D10 — Add a reusable cyclic curriculum probe

**Choice.** Keep `workspace/probe_curriculum.py` with dynamic imports of
`CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`.

**Rationale.** The shared production census samples the actual sampler but does
not exhaust every start of a small deterministic schedule. The local probe is
cheap enough to run after each schedule/rival edit.

**Alternatives rejected.** Hard-coding rival names into a one-off script would
drift from generator declarations. Treating the Python mirror as authority was
rejected; the tool states that it complements Racket-labeled checks.

**Probe and limitation.** Final run used four seeds, three bands, 24 starts,
288 windows, and 1,152 rotations with zero declared-rival ambiguity. Overlapping
windows produced 156 unique inputs; that denominator is reported separately.
