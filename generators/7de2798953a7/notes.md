# Working notes: 7de2798953a7

## Review repair `review-24e4a642d527e4f2`

No prior return was used as a design lead. The task's associated-notes file was
empty, so the repair was derived from the pinned baseline, canonical pairs,
actual Racket authority, and retained probes.

The baseline declared nine axes but consumed only a subset. Four helpful
textures were byte-identical to the default, negative fixtures leaked into the
ordinary texture domain, singleton axes could not be probed, and `RULE_HASH` was
missing. More importantly, all four canonical pairs also fit a plausible rival:
fill alternating cells between any two nonzero row endpoints, without requiring
the endpoint colours to match.

Version 3.0.0 keeps the Racket authority unchanged and replaces the sampler with
three exact controls. Default `(height, width, n_pairs)` cycles through the exact
canonical profiles. Slot `sample_index % 3 == 0` is canonical; the other two
slots add one unequal-colour endpoint row. Thus every four consecutive examples
contain at least two equality witnesses, and every possible one-query holdout
from that four-example window leaves at least one witness among the three demos.
The first valid pair always has an odd span; the second, when present, has an
even span. This distinguishes left- from right-anchored alternation. Difficulty
changes span composition only: easy chooses the shortest legal span, hard the
longest, and medium/default retains seeded variety.

Executable contracts cover solid fill, right-anchored phase, and the
any-two-nonzero shortcut. `self_check`, exact override observation, the
independent oracle, cyclic schedule audit, and real-Racket parity probe live in
`tests/` and `workspace/`.

Final generator SHA-256:
`8d2e04b1455b242f0212529c123d54c5e8e5f258c16b821c31c5a33c31d320e5`.
The canonical authority and authority-set hash were not changed.
## Current reviewer considerations

Source SHA-256: `8d2e04b1455b242f0212529c123d54c5e8e5f258c16b821c31c5a33c31d320e5`.

# Decisions for `7de2798953a7`

## D1. Keep the reference authority unchanged

**Input choice.** Pin `RULE_HASH = "3bca54d68914"` and leave canonical/base
Racket source untouched.

**Rationale.** The canonical outputs, independent Python oracle, and actual
Racket execution agree. The defect was in sampling and teaching, not labels.
Changing the rule would have expanded scope without a counterexample to the
existing authority.

**Alternative rejected.** Generalize the rule to fill unequal-colour endpoints
using one endpoint colour. That is precisely the canonical-fitting shortcut the
repair needs to disprove, not a justified authority change.

**Probe.** Four canonical pairs plus the exact shortcut witness and twelve final
generator samples were compared against real Racket: 17/17 matched
(`checks/distribution-audit-final.json`).

## D2. Remove inert and negative-fixture axes

**Input choice.** Advertise only `grid_h`, `grid_w`, and `n_pairs`.

**Original rationale.** Unknown. The baseline declared `palette_kind`,
`palette_size`, `n_distinct_colors`, `position_bias`, `density`, and `texture`,
but several were singleton, unused, or aliases; helpful textures were
byte-identical and negative fixtures were declared ordinary valid values.

**Alternatives rejected.** Keeping the names as diagnostic controls would retain
an API with no observable effect. Turning negative fixtures into ordinary draws
would mix malformed examples into the training domain. Adding artificial
palette remapping would not teach the row rule and would complicate exact
canonical-profile support.

**Probe.** Shared baseline lint and defect lint reproduced all issues. Final
standalone lint and override stages pass, and focused tests cover both boundaries
and bad types/unknown keys.

## D3. Preserve exact canonical default profiles

**Input choice.** Cycle default `(h, w, n_pairs)` through `(6,7,3)`, `(5,8,3)`,
`(4,9,2)`, and `(4,8,2)`. With background, these yield the four exact canonical
palette-size profiles.

**Rationale.** This guarantees profile-floor support in every band while keeping
shape and palette close to the source task. Exact overrides still permit heights
4..10, widths 7..14, and 1..4 valid pairs.

**Alternative rejected.** Broad random defaults would increase superficial
variety but could make canonical support rare. A single fixed profile would pass
one floor but unnecessarily collapse source diversity.

**Probe.** All 600 independent default draws and all 60 battery profile-floor
draws hit an exact canonical profile. The four expected shapes appear in every
band.

## D4. Use a `canonical, contrast, contrast` schedule

**Input choice.** Slot 0 modulo 3 has only valid same-colour pairs. Slots 1 and 2
add one unequal-colour endpoint row.

**Rationale.** The strongest plausible rival fills between any two nonzero
endpoints. One contrast row is a minimal lawful counterexample. Two contrasts
per three-slot cycle ensure any four consecutive examples retain a witness after
any one is selected as query.

**Alternatives rejected.** Purely random distractors give no lesson-level
coverage guarantee. A single contrast slot per cycle fails when that slot is the
query. Contrast in every scene needlessly abandons the clean canonical domain
and could teach that distractors are mandatory.

**Probe.** One hundred cyclic starts per band and all four query positions gave
0/1,200 failures. The source-bound census materialized 300 lessons and rotated
all 1,200 pairs with zero ambiguity.

**Failure mode.** Arbitrary downstream shuffling or skipped indices can destroy
the schedule. The gate must be run after actual lesson assembly in that case.

## D5. Force a phase witness in every draw

**Input choice.** The first valid pair has an odd endpoint span; the second has
an even span when present.

**Rationale.** Odd spans make left- and right-anchored alternation disagree.
Including an even span as well avoids narrowing all pairs to one parity.

**Alternatives rejected.** Relying on random parity leaves some lessons
compatible with the wrong phase. Solid fill is separately refuted by every
fillable pair.

**Probe.** All 600 independent draws contained an odd-span witness and disagreed
with both solid-fill and right-phase rivals.

## D6. Make difficulty compositional, not a separate law

**Input choice.** Easy selects the shortest legal span, hard the longest, and
medium/default a keyed random legal span. Shape, pair count, palette profile, and
curriculum schedule stay unchanged.

**Rationale.** This gives the knob an observable and semantically reasonable
effect without allowing band to predict a different rule or removing canonical
support.

**Alternative rejected.** Varying grid size or pair count by band would conflict
with exact profile support; varying only RNG salt did not satisfy the detector
because it could remain semantically indistinct.

**Probe and failed attempt.** The first repair ignored difficulty and was caught
by shared `dead-bands` lint. Twelve test-first band comparisons failed before the
fix; the retained intermediate battery records the same root cause. The final
55-test suite and full battery pass.

## D7. Keep colours distinct on valid rows

**Input choice.** Valid pair colours are sampled without replacement from 1..9;
a contrast row reuses or supplements those colours but has unequal endpoints.

**Rationale.** Distinct valid colours make row membership visually unambiguous
and reproduce canonical palette-size profiles. Reusing colours across valid rows
would add a grouping question unrelated to the reference transformation.

**Alternative rejected.** Restricting to baseline colours 2..9 lacked a rule
basis; colour 1 is lawful and increases harmless palette coverage.

## D8. Add executable contracts and reusable probes

**Input choice.** Declare semantic witnesses/rivals, canonical shortcut, exact
observer, strict validator, 55 focused tests, an independent oracle, and a cyclic
schedule/Racket audit tool.

**Rationale.** A prose claim that the schedule teaches the rule is too weak.
Executable rivals make the intended finite claim reproducible, while the
independent oracle avoids validating Python construction against itself.

**Limitation.** The competitor set is finite. It verifies named failure modes,
not universal induction. `audit_distribution.py` states this limit explicitly.

## Prior evidence used

No prior return was used as a lead. `evidence/associated_notes.jsonl` for this
task was empty. The pinned baseline, canonical ledger, actual Racket execution,
and newly retained before/intermediate/final measurements were used instead.
