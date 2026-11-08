# Working notes: e0650802a8fb

## Baseline finding

Baseline generator SHA-256 was
`d4ea3d0b659ab327a2131cc68d2f916da79a55e7b168c6a67fbe9202a86f405e`
(version 1.1.0). Its distribution avoided all diagonal intersections and its
validator rejected lawful canonical overlaps. The baseline battery therefore
failed lint (missing `RULE_HASH` plus two dead single-token axes), self-check
(two canonical overlap inputs rejected; mutation sensitivity 40/58), and strict
defect lint (four dead texture controls plus degenerate textures mixed into the
ordinary domain). The morphology-only distribution gate passed, illustrating
why that diagnostic was insufficient for this task.

## Authority interpretation

The canonical Racket rule was not changed. It processes nonzero colors in
row-major first-appearance order. A color acts only when it appears exactly twice
and those two cells lie on a non-trivial 45-degree diagonal. Its inclusive span
is painted into the accumulating output, so a later color owns a shared cell and
may overwrite an earlier color's original endpoint.

This row-major collision behavior was the root cause of the baseline validator
failure: overlap was lawful, not an ambiguity to reject.

## Repair

The selected generator is now version 3.0.0 and pins rule hash `040cfb38300e`.
The old loosely advertised controls were replaced by four exact, observable axes:
`grid_h`, `grid_w`, `pair_count`, and `scene_profile`. Five deterministic semantic
profiles cover disjoint spans, interior crossings, both endpoint-overwrite
outcomes, and inert rule-guard controls. D4 transformations, canvas placement,
colors, and extra disjoint paths still vary the concrete grids.

The controls profile adds exactly one axis-aligned pair, one singleton, and one
three-cell color. These cases teach that the rule requires both a diagonal and
exactly two cells. Seven executable rivals and seven witness predicates are bound
to the generator, and `lesson_identifiable` rejects any lesson whose five
demonstrations leave a declared rival alive.

## Test-first repair history

The first focused tests failed on the absent `RULE_HASH` and canonical-overlap
rejection. After the initial implementation, the exhaustive override gate found
347 failures: controls scenes reconstructed their 8×8 template origin from only
the selected target paths, which can shift after rotation when `pair_count=2`.
A regression test was added for an independently overridden dimension, then the
layout function was changed to return its selected frame origin directly. The
rerun accepted 18,090/18,090 draws across 201 override cases and three bands.
The failed iteration is retained under `checks/targeted-override/`; the passing
rerun is under `checks/targeted-override-r2/`.

## Final evidence

Final generator SHA-256:
`9edaeb09de4a1961f9556220121fc4ee8ab4d09a3ca626c568ba7f03da5e6abc`.

- `checks/after/checks/e0650802a8fb_after_battery_summary.json`: all 12 required
  stages green, with no failed, interrupted, or pending stage.
- `checks/e0650802a8fb-lesson-probe.json`: 5/5 canonical pairs accepted and
  mirrored; 5/5 exact-axis cases; 300/300 cyclic windows profile-complete,
  rival-complete, and identifiable.
- `checks/lesson-census-final.json`: 100/100 lessons materialized per band,
  0 ambiguous, 0 hook warnings, 0 scoring errors, and every declared rival
  refuted in all 100 lessons per band.
- `solve/summary.json`: post-repair visible-only solve used the final generator
  hash and passed all five visible demonstrations in one revision; prior exposure
  was declared `yes`, and no reference was consulted during the solve.

## Limits

The rival set is finite and does not prove universal identifiability. The
production census uses consecutive demonstrations plus a query and does not test
every cyclic query rotation; the workspace probe compensates by checking every
cyclic start of the five-profile demonstration schedule. Controls intentionally
occupy 20% of schedule positions and fall outside `strict_canonical_like`, leaving
a measured strict rate of 469/600 (78.2%), above the declared 0.75 floor.

Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `9edaeb09de4a1961f9556220121fc4ee8ab4d09a3ca626c568ba7f03da5e6abc`.

# Decisions for e0650802a8fb

## D1 — Keep the canonical Racket authority unchanged

**Decision.** Pin `RULE_HASH = "040cfb38300e"` and repair the generator,
validator, mirror, and curriculum around the selected authority.

**Rationale.** Canonical examples that the baseline rejected are lawful under the
existing program. The key behavior is row-major first-appearance order with
later painting owning a shared cell. There was no evidence of a wrong authority;
the defect was the generator's narrower interpretation.

**Rejected alternative.** Continue prohibiting all overlap. That would preserve
the baseline's simple distribution but contradict canonical train/test inputs and
hide collision priority.

**Failure mode guarded.** A future authority change now trips the pinned hash,
canonical parity tests, rule smoke mirror comparison, and authority sync.

## D2 — Use five explicit semantic profiles instead of unconstrained random pairs

**Decision.** Assemble every five consecutive samples from the profiles
`disjoint`, `interior_cross`, `endpoint_overwrite`, `endpoint_survive`, and
`controls`.

**Rationale.** The lesson assembler uses five demonstrations. A deterministic
semantic cover guarantees that every complete lesson contains the necessary
witnesses; merely observing each profile often in a pooled sample would not prove
that any particular lesson teaches the rule.

**Rejected alternatives.** Uniformly random diagonals made rare endpoint
crossings unreliable and could leave a full lesson ambiguous. A fixed list of
five literal grids would teach the examples rather than the rule. The chosen
middle ground fixes semantic roles while varying transformations, placement,
colors, dimensions, and extra paths.

**Probe.** `workspace/lesson_probe.py` checks all five cyclic starts, not just
start zero. With 20 seeds and three bands, all 300 windows were complete and
identifiable.

## D3 — Teach both collision outcomes

**Decision.** Keep separate `endpoint_overwrite` and `endpoint_survive` profiles,
in addition to an interior crossing.

**Rationale.** Endpoint crossings distinguish the real accumulated-paint
semantics from endpoint-preserving shortcuts. The two order outcomes prevent a
simpler claim such as “shared original endpoints are always overwritten.” The
interior crossing is color-assigned so row-major priority disagrees with numeric
ascending order; endpoint scenes also refute numeric descending order.

**Rejected alternative.** A single generic `crossing` profile would not expose
which cell owns the collision or whether original endpoints are protected.

## D4 — Add one tightly specified controls grammar

**Decision.** A controls scene contains exactly one axis-aligned pair, one
singleton, and one three-cell color, alongside 2–4 valid diagonal pairs.

**Rationale.** Two plausible shortcuts fit all five canonical pairs:
`fill_axis_pairs_too` and `outermost_cells_even_when_repeated`. The axis pair
teaches the 45-degree requirement; the triple teaches the exactly-two guard; the
singleton prevents a broad “all colors expand” reading. Keeping exactly one of
each makes the profile recoverable and testable.

**Rejected alternatives.** Mixing arbitrary counts/geometries created validator
ambiguity. Treating these as negative/degenerate textures would keep them out of
ordinary lessons and fail to teach the guards.

**Known limit.** Controls are deliberately outside the strict canonical-like
profile, so the measured strict fraction is 469/600 (78.2%), not 100%. This is
above the declared `MIN_STRICT_FRAC = 0.75` and reserves 20% of the schedule for
rule disambiguation.

## D5 — Advertise only exact, observable axes

**Decision.** Replace the baseline's broad/dead metadata with `grid_h`, `grid_w`,
`pair_count`, and `scene_profile`.

**Rationale.** Every advertised override must change or constrain the returned
input and be recoverable by `observe_overrides`. Unknown and invalid keys are
rejected rather than silently ignored.

**Rejected alternative.** Retain `palette_kind`, `density`, `position_bias`, and
texture aliases for nominal combinatorics. Baseline evidence showed these were
ignored or single-token pseudo-axes; keeping them would make the API dishonest.

**Retained failure.** The first implementation inferred the controls frame from
selected endpoints. The exhaustive gate found 347 failures after rotations and
small pair counts. Returning the selected frame origin directly fixed the source
of error; see R3 evidence.

## D6 — Use D4 templates plus keyed variation

**Decision.** Define small semantic templates and vary them through all eight D4
symmetries, legal frame placement, keyed color assignments, dimensions, pair
counts, and extra disjoint paths.

**Rationale.** This gives reliable witnesses without collapsing to a tiny set of
byte-identical grids. Final diversity measured 100% unique inputs and outputs in
300 pair instances.

**Rejected alternative.** Fully procedural intersection search was more complex,
harder to validate, and unnecessary for this bounded task. Literal untransformed
templates were too easy to memorize.

## D7 — Bind rivals and witnesses to source

**Decision.** Declare seven executable `LESSON_COMPETITORS`, corresponding
`SEMANTIC_WITNESSES`, and the two `CANONICAL_SHORTCUTS` in the generator. Make
the workspace probe iterate those declarations.

**Rationale.** A prose claim that the curriculum is identifiable is weak. An
executable rival can be checked against canonical pairs and every generated
lesson. Reading declarations dynamically avoids drift between source and probe.

**Rejected alternative.** Hard-code a duplicate rival-name list in the probe.
That would allow future generator edits to silently leave the authoring check
stale.

**Limit.** The list is finite. Passing it is evidence against named plausible
shortcuts, not a universal proof of identifiability.

## D8 — Keep the production census and cyclic probe separate

**Decision.** Run 100 production lessons per band and also retain a smaller
source-bound cyclic-start probe.

**Rationale.** The production census validates the real sampler/materializer and
records 300 lessons, but it does not rotate every pair into each lesson role. The
cyclic probe cheaply covers all schedule starts and exact controls. The two tools
answer different questions and agree on the declared rivals.

**Rejected alternative.** Treat a passing small battery sample as sufficient.
The assignment explicitly notes that plausible canonical-fitting rivals warrant
at least 100 lessons per band.

## D9 — Preserve failures and distinguish orchestration from semantics

**Decision.** Retain the interrupted before aggregate, the interrupted first
after aggregate, the raw pytest import error, and the first override failure.
Only the completed final aggregate is reported as 12/12 green.

**Rationale.** A running/interrupted summary is not a pass. The retained artifacts
make it clear which failures were source defects, which were a test-environment
issue, and which were outer orchestration limits.

## D10 — Do not patch audit targets

**Decision.** Produce reproducible findings for `90745f7073da` and
`1e41c90ec2dc` without editing either target.

**Rationale.** The assignment asks for adversarial review only. Both witnesses
are outside the targets' documented generated domain but lawful under canonical
authority; that distinction is recorded rather than overclaiming an ordinary
sample violation.

## D11 — Final handoff and replay

**Decision.** Package only the allowed selected-task delta and reports, apply the
packaged patch to a fresh extraction, verify the generator hash, and rerun the
focused tests there.

**Rationale.** This checks the actual handoff artifact rather than only the
working tree. Exact replay commands and evidence are recorded in `RESULTS.json`.
