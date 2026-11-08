# Working notes: e4c4a1290088

## 2026-10-04 review-a0c2189a1767a9f8

Baseline `2.1.0` preserved the selected rule but had stale generic metadata:
missing `RULE_HASH`, dead texture/palette aliases, difficulty-specific override
ranges that contradicted the advertised domains, silent unknown-key acceptance,
no canonical-profile prior, and no executable semantic teaching contract.

The `3.0.0` rewrite keeps the Racket authority unchanged and narrows the public
surface to three exact axes. It constructs each header pair so that every
nonzero label appears on both axes, an off-diagonal equality is guaranteed, and
a nonzero mismatch is guaranteed. Those witnesses refute `diagonal_only`,
`first_label_only`, and `any_nonzero_pair` rivals in every generated example.

Retained evidence:
- before battery: `checks/before/checks/e4c4a1290088_before_battery_summary.json`
- final battery: `checks/after/checks/e4c4a1290088_after_battery_summary.json`
- 300-lesson census: `checks/lesson-census-final.json`
- cyclic query rotations: `checks/cyclic-lesson-probe-final.json`
- focused regressions: `tests/test_generator.py`

Limit: named rivals and finite sampling do not prove universal identifiability;
novel shortcuts remain possible. Broad profile draws are intentionally less
canonical than the three scheduled profiles, while all remain within the same
header-equality grammar.
## Current reviewer considerations

Source SHA-256: `6c19b72c865c40ad7ad2792e3ee0f94616a4597a1fcad93133e372998db2cc86`.

# Decisions for `e4c4a1290088`

Final generator SHA-256:
`6c19b72c865c40ad7ad2792e3ee0f94616a4597a1fcad93133e372998db2cc86`.
The canonical Racket authority was not changed.

## D1 — Preserve the equality rule; repair the data contract

**Choice.** Keep the canonical transformation exactly: preserve the header row
and column, then place the column-header color in an interior cell iff it equals
the row-header color.

**Original rationale.** The baseline comments described this rule and the
before `rule_smoke` and `authority_sync` stages were already green. The original
reason for the surrounding generic texture/palette API is unknown; the current
source did not make those controls observable.

**Alternatives considered.** Changing the Racket rule, admitting nonzero input
interiors, or treating degenerate no-header/no-match fixtures as normal data.
All were rejected because they either alter authority or weaken the teaching
grammar without solving the measured metadata defects.

**Probe.** Canonical pairs are accepted by `self_check`; the Python oracle
matches every official output; final `rule_smoke` and `authority_sync` pass.

**Failure mode / limit.** A Python oracle can drift later; the source-bound
battery remains the authority check and must continue to run.

## D2 — Replace stale aliases with three exact axes

**Choice.** Advertise only `grid_h` in 6–18, `grid_w` in 6–18, and `n_labels` in
2–5. All values are legal in every difficulty band, exact overrides are
observable through `observe_overrides`, malformed values fail loudly, and
unknown keys are rejected.

**Original rationale.** Baseline axes included dead `texture`/palette aliases,
fixed descriptive enums presented as controls, multiple names for color count,
and ranges inconsistent with band-specific draw bounds. The before override
contract measured 18,631 findings across 119,880 draws and accepted an unknown
key.

**Alternatives considered.** Preserve aliases for compatibility; declare a
large incompatibility matrix; or make axis ranges band-dependent. Aliases were
rejected because they were not semantically distinct. Declared incompatibilities
would hide avoidable API failures. Band-dependent public validity was rejected
because an exact axis should mean the same thing in every band.

**Probe.** Thirty-eight focused tests exercise boundary and joint overrides in
all bands. The final shared contract accepts 27,540/27,540 draws over 306 cases
with zero explicit incompatibility rejections.

**Failure mode / limit.** Removing aliases is an API change for callers that
used undocumented/stale names. The return intentionally favors a truthful,
small training-data contract over silent compatibility.

## D3 — Interleave canonical profiles with broad draws

**Choice.** Use `sample_index % 4`: slots 0–2 select the three official
shape/label profiles `(6,6,3)`, `(7,7,2)`, and `(8,8,3)`; slot 3 uses a
band-scaled broad draw. Exact user overrides take precedence.

**Original rationale.** The baseline had 0/60 exact canonical-profile hits,
with zero support in medium and hard. A deterministic schedule makes support
falsifiable and avoids hoping a random sampler lands on narrow profiles.

**Alternatives considered.** Canonical-only generation; a low-probability random
canonical prior; or separate profile names as another axis. Canonical-only was
rejected as too narrow. A random prior can miss the 20-draw gate. Another axis
would enlarge the override surface without changing the task grammar.

**Probe.** The final floor records 46/60 exact hits—17 easy, 16 medium, 13 hard—
and focused tests observe all three profiles within 12 samples of every band.

**Failure mode / limit.** The periodic schedule is discoverable. The fourth slot
retains broad size and label variation, but a nonperiodic stratified scheduler
could reduce this artifact in a future shared sampler.

## D4 — Use the same complete nonzero label set on both axes

**Choice.** Draw 2–5 distinct nonzero ARC colors; place every label at least once
in both header strips; optionally include zero headers where profile capacity
allows. Preserve the all-zero interior and zero corner.

**Original rationale.** Equality is easiest to infer when each label has both a
positive branch and contrasts against another nonzero label. Matching label
sets also keep `n_labels` exactly observable rather than allowing one-sided
colors that never participate in a positive equality.

**Alternatives considered.** Independent row/column palettes; a single label;
all nonzero headers; or zero-heavy headers. Independent palettes can create
unused labels and no positive examples. One label hides mismatch behavior.
Always excluding zero misses a harmless canonical feature; always forcing zero
would distort the 6×6 profile.

**Probe.** `self_check` requires equal label sets, 2–5 labels, an off-diagonal
match, and a nonzero mismatch. Every official pair is accepted.

**Failure mode / limit.** This is stricter than the mathematical rule, which
could operate on unequal label sets. It is an intentional teaching-domain
restriction, not a claim about the full function domain.

## D5 — Construct witnesses instead of relying on rejection sampling

**Choice.** Guarantee an off-diagonal equality by placing the first label at
column-header position 1 and row-header position 2, while the complete
multi-label sets guarantee nonzero mismatches.

**Original rationale.** The baseline loop tried up to 60 random layouts and then
used a fallback. Constructive placement is deterministic, cheap, and guarantees
that every returned scene teaches both branches.

**Alternatives considered.** Continue rejection sampling; accept scenes without
an off-diagonal match; or force a whole diagonal. Rejection sampling complicates
provenance and can fail at boundaries. Diagonal-only evidence admits the exact
shortcut the generator should refute.

**Probe.** All three semantic witnesses fire in 600/600 battery draws. Each
named rival disagrees with the oracle on every one of 128 focused default draws
and on all retained lesson probes.

**Failure mode / limit.** The fixed `(2,1)` witness location is a minor position
artifact. It is not sufficient to reproduce the complete output, because all
labels recur in randomized positions, but randomizing this guaranteed pair is a
reasonable future refinement.

## D6 — Declare executable rivals and lesson identifiability

**Choice.** Add `SEMANTIC_RIVALS`, `WITNESS_RIVALS`,
`LESSON_COMPETITORS`, and `lesson_identifiable` for:
`diagonal_only`, `first_label_only`, and `any_nonzero_pair`. Require two demos.

**Original rationale.** The before semantic gate reported `NO_CONTRACT`; visual
diversity alone does not show that a lesson excludes plausible wrong rules.

**Alternatives considered.** Depend only on generic geometric transforms; list
rivals only in prose; or require three demos. Generic transforms do not target
the task's specific logic. Prose is not executable. Two demos are sufficient
because each generated example independently contains all three witnesses.

**Probe.** Final semantic gate: 3/3 canonical accepted, 12/12 lessons
identifiable, three witness/rival claims verified. Production census: 300/300
lessons with every declared rival refuted. Cyclic probe: 900/900 rotations.

**Failure mode / limit.** Declared rivals are finite and reviewer-authored;
undeclared shortcuts can survive. `QUESTION_ANSWER.md` proposes a shared
metamorphic deconfounding gate to discover one important class automatically.

## D7 — Separate strict canonical likeness from lawful broad generation

**Choice.** `strict_canonical_like` recognizes the three official profiles and
sets `MIN_STRICT_FRAC = 0.50`, while `self_check` accepts broader 6–18 grids in
the same grammar.

**Original rationale.** Training needs both authority-proximal support and
variation. Conflating the two either excludes useful broad examples or makes a
strict-profile metric meaningless.

**Alternatives considered.** Mark every lawful scene strict; make all draws
canonical; or opt out of the profile floor. Those alternatives either inflate
the metric, collapse diversity, or preserve the measured baseline gap.

**Probe.** Observed strict rate is 462/600 = 77.0%, with per-band rates 86.0%
easy and 72.5% in both medium and hard. Broad rejections are explicit profile
reasons, not self-check errors.

**Failure mode / limit.** The 50% floor is task-local judgment, not a universal
optimal training mixture. Downstream evaluations should still compare mixture
weights.

## D8 — Retain focused regressions and add cyclic query coverage

**Choice.** Add 38 task-local tests and a reusable
`workspace/cyclic_lesson_probe.py` that reads the live competitor declarations,
builds deterministic three-pair windows, and rotates each pair through the query
position.

**Original rationale.** The required shared census explicitly does not rotate
query positions, and the general battery does not automatically discover task
local tests.

**Alternatives considered.** Rely on the 12-lesson smoke sample or duplicate a
hard-coded rival-name list. Both were rejected: the sample is underpowered, and
a copied list can silently drift from generator declarations.

**Probe.** Portable task tests pass 38/38. The production census reports 900
unique inputs; the task-local probe reports 900 rotations, 900 unique inputs,
and zero failures.

**Failure mode / limit.** The cyclic probe uses deterministic task-local windows
rather than the production materializer; it complements rather than replaces
the source-bound census.
