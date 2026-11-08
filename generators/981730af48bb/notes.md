# Working notes: 981730af48bb

## Rule and review scope

The unchanged authority transforms each lawful row independently: two equal,
nonzero endpoints at a positive even horizontal distance are erased and replaced
by one dot of the same color at their integer midpoint. Background is zero and
all empty rows remain empty. `RULE_HASH = "250fc3187c8a"` pins the reviewed
canonical rule. No Racket source or canonical puzzle row was changed.

The baseline generator had three classes of contract failure:

1. It omitted `RULE_HASH`, advertised inert single-valued and palette/texture
   controls, accepted unknown overrides, and exposed negative fixtures as normal
   generation values.
2. Its normal sampler scarcely covered the public task envelope: only 3/60
   baseline draws matched the canonical envelope and medium/hard had zero support.
3. It declared no semantic contract, no executable shortcut rivals, and no
   lesson-level identifiability check.

The baseline 12-stage battery therefore ended at 7 green, 2 advisory, and 3
failed stages. See
`checks/before/checks/981730af48bb_before_battery_summary.json`.

## Final generator design (2.1.0)

### Truthful axes

Only four pixel-recoverable axes remain:

- `grid_h`: 4..12
- `grid_w`: 6..16
- `pairs`: 2..4 generated active rows
- `span_profile`: `short`, `wide`, or `canonical`

Every Cartesian combination is constructively supported in every difficulty
band. Unknown keys, old dead keys, wrong types, and out-of-range values fail
loudly. `observe_overrides()` recovers the exact advertised values from the
returned grid and generation asserts the round trip.

`self_check()` intentionally accepts one active row as part of the rule domain,
but the generator advertises and emits 2..4. A one-row lesson cannot refute the
plausible “process only the first active row” shortcut, so it is unsuitable for
this training curriculum even though it is a lawful isolated puzzle input.

### Span profiles and public-shape support

- `short` gives every active row span 2.
- `wide` gives every active row the greatest positive even span fitting the
  selected width.
- `canonical` alternates spans 2 and 4 by active-row index.

The per-row 2/4 mixture is deliberate. The public examples require both spans
and, more importantly, a mixed grid refutes “infer the first row's offset and
reuse it everywhere.” The first repaired implementation (2.0.0) used one span
for an entire grid. It passed the ordinary gates, but self-review found that it
still missed this structural property. That intermediate evidence is retained
under `checks/intermediate-v2.0.0/`, and the stale solve is under
`checks/prior-solve/uniform-span-v2.0.0/`.

### Default curriculum

The deterministic four-position cycle is:

1. canonical size 5x7, two pairs, canonical mixed spans;
2. canonical size 4x6, two pairs, canonical mixed spans;
3. canonical size 5x8, two pairs, canonical mixed spans;
4. a difficulty-aware broad draw, cycling short/wide/canonical span profiles.

Thus every 3-demo + 1-query lesson window has public-scale support while still
covering larger grids, 2/3/4 active rows, and short/wide cases. Active rows and
endpoint positions are randomized. Pair colors are sampled without replacement,
so generated scenes use distinct row colors; the validator and rule mirror do
not require distinct colors.

That color choice is a remaining finite-distribution restriction, not a claimed
rule invariant. It teaches per-row color preservation strongly, but these tests
do not prove induction to repeated endpoint colors across different rows.

### Semantic contract

`rule_mirror()` independently implements the row-wise midpoint transformation.
Eight named competitors cover endpoint retention, segment fill, fixed inner-cell
choices, first-color reuse, first-row-only processing, span-4-only processing,
and first-row-offset reuse. Six semantic witnesses connect scene properties to
those rivals. `lesson_identifiable()` rejects any 3-demo lesson in which a named
competitor still fits every demonstration.

The task tests check every leave-one-out query rotation in each four-pair window;
the source-bound lesson census repeats that at larger scale. These are finite
rival checks, not a proof that no undeclared shortcut exists.

## Verification summary

Final generator SHA-256:
`1b39f28ec3a84046c570ec2b2d7ad5e89bcad5b8320c9cc502607691b4eae277`.

- Required final battery: 12/12 green.
- Task-local tests: 26/26 passed.
- Lesson census: 300/300 lessons materialized, 1,200 labelled pairs,
  1,200/1,200 leave-one-out rotations identifiable, zero declared-rival
  ambiguities, 1,186 unique inputs.
- Post-repair visible solve: 3/3 demonstrations passed in one revision; earlier
  repair exposure declared, no reference consulted during the solve.

See `REVIEW.md`, `DECISIONS.md`, and `RESULTS.json` in the returned review for
exact commands and retained evidence.
## Current reviewer considerations

Source SHA-256: `1b39f28ec3a84046c570ec2b2d7ad5e89bcad5b8320c9cc502607691b4eae277`.

# Decisions for 981730af48bb

## D1 — Preserve the authority; repair only the sampler and its contracts

The selected Racket authority already expresses the intended row-wise midpoint
rule and agrees with all canonical examples. I therefore pinned
`RULE_HASH = "250fc3187c8a"` and changed no Racket source, canonical row, approval
label, or shared tool. Rewriting the authority would have added risk without
addressing any observed generator defect.

## D2 — Advertise only exact, pixel-recoverable axes

The final axes are `grid_h` 4..12, `grid_w` 6..16, `pairs` 2..4, and
`span_profile` in `short|wide|canonical`. Every advertised cross-product is
constructive in easy, medium, and hard bands, and `observe_overrides()` recovers
the exact values from the output grid.

Rejected alternatives:

- Keep palette, palette-size, color-count, density, position-bias, or texture
  controls. Baseline evidence showed those controls were dead, single-valued,
  mutually inconsistent, or negative fixtures masquerading as normal data.
- Keep unknown-key compatibility. Silent acceptance makes misspelled experiments
  look valid, so final generation rejects unknown and legacy keys.
- Keep pair count 1 as an advertised training axis. It is lawful under
  `self_check`, but cannot teach that all active rows must be processed. The
  generated curriculum therefore uses 2..4 while the validator remains faithful
  to the broader one-row rule domain.

## D3 — Use three span profiles, with mixed 2/4 spans as canonical

`short` is distance 2, `wide` is the maximum even distance fitting the row, and
`canonical` alternates distances 2 and 4 across active rows. The mixed profile
matches the structural content of the public examples and refutes the tempting
shortcut “reuse the first row's half-span everywhere.”

I rejected the first repaired uniform-span design even though it passed the
ordinary battery. A self-review against the actual public grids found that its
within-grid support was narrower than the task. The failing test was written
first, then the sampler, rival, witness, and schedule were updated. Retained
intermediate evidence is in `checks/intermediate-v2.0.0/` and the final red/green
cycle is in `checks/tdd-red-mixed*` and `checks/tdd-green-canonical*`.

## D4 — Use a deterministic four-role lesson cycle

Each lesson consists of three demonstrations and one query. Three positions use
the public size profiles 5x7, 4x6, and 5x8 with two mixed-span pairs. The fourth
is a difficulty-aware broad draw: easy uses smaller two-pair scenes, medium uses
three pairs, and hard uses four; its span profile cycles through short, wide, and
canonical.

This makes every contiguous four-pair lesson include public-scale support while
retaining broader geometry. Task tests and the census hold each of the four pairs
out as query, preserving demonstration order, so identifiability is not tied to
one fixed query slot.

Rejected alternatives:

- Pure random sampling: it can produce long runs without a mixed-span witness.
- Canonical-only sampling: high fidelity but poor size/pair-count coverage.
- Treating semantic-gate `NO_CONTRACT` as acceptable: correct individual labels
  do not establish a useful lesson.

## D5 — Keep row colors distinct in generated data, but do not make it a rule

Colors are sampled without replacement for 2..4 active rows. This cleanly teaches
that each row preserves its own color and supplies strong witnesses against a
first-color shortcut. `self_check()` and `rule_mirror()` do not reject repeated
colors, because the rule itself does not require uniqueness.

Remaining limitation: the default sampler does not test repeated colors across
different active rows. The finite rival/census evidence therefore supports the
advertised curriculum, not universal induction over every lawful coloring.

## D6 — Declare executable rivals rather than prose-only expectations

Eight competitors are executable and named in both `SEMANTIC_RIVALS` and
`LESSON_COMPETITORS`: keep endpoints, fill the segment, select either inner cell,
reuse the first color, process only the first row, process only span four, and
reuse the first row's half-span. Six witness predicates explain which scene
feature defeats each family.

The large final census tested 300 lessons, 1,200 pairs, and all 1,200 query
rotations. Zero declared competitor survived the demonstrations while changing a
query. This is strong regression evidence, but an undeclared hypothesis can still
exist; the audit findings motivate the counterfactual shortcut gate proposed in
`QUESTION_ANSWER.md` and `FEEDBACK_TO_CODEX.md`.

## D7 — Preserve failures and bind claims to final bytes

The final generator hash is
`1b39f28ec3a84046c570ec2b2d7ad5e89bcad5b8320c9cc502607691b4eae277`.
The stale 2.0.0 solve and intermediate checks were retained rather than relabelled.
A new solve episode was prepared from the final bytes and records prior rule
exposure honestly. The final source patch is replayed on a pristine extraction
before packaging; its exact commands, hash checks, and focused test result are
recorded in `RESULTS.json` and `checks/final-handoff/`.
