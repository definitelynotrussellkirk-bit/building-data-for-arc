# Working notes: 8dbffe99308f

## Baseline finding

The selected 2.0.1 sampler generated only 3–7 isolated cells strictly above
the anti-diagonal. It omitted `RULE_HASH`, exposed collapsed/unprobed metadata,
and never exercised below-side sources, occupied reflected partners, axis
fixed points, exact controls, or lesson-level identifiability. The five
canonical pairs themselves also admit at least two plausible wrong rules:
`above_only` and `fill_empty_only`.

The interrupted before battery is retained under `checks/before/`; it records
the missing authority hash and collapsed axes before the host-side command
ended during defect lint. No prior associated review was used as evidence;
`evidence/associated_notes.jsonl` was empty.

## Selected repair

Version 3.1.0 keeps the Racket authority unchanged and pins
`RULE_HASH = e248d283a2c2`. Public axes are now only `size` (6..10) and
`markers` (4..10), both exact and recoverable from pixels. `self_check`
validates shape, ARC colors, marker/color counts, off-axis support, and at most
one unequal occupied mirror pair. The Python oracle reads from an immutable
snapshot, matching the canonical swap behavior when both partners are occupied.

The deterministic six-slot curriculum alternates ordinary and unequal-conflict
profiles:

1. `above_sparse`
2. `unequal_conflict_below`
3. `above_with_axis`
4. `unequal_conflict_mixed`
5. `below_sparse`
6. `unequal_conflict_with_axis`

This alternation gives every three consecutive demonstrations at least one
conflict and every four consecutive pairs two conflicts. Conflict coordinates
are randomized over legal anti-diagonal orbits rather than fixed to a special
location.

## Intermediate failure that changed the design

The first 3.0.0 repair had one conflict profile in some four-pair windows.
Production ordering was unambiguous, but the 300-lesson rotated census found
201 ambiguous rotations out of 1,200: holding out the sole conflict let
`fill_empty_only` fit all three demonstrations. Evidence is retained in
`checks/lesson-census.json` and `checks/tdd-red-rotations/`. The alternating
3.1.0 schedule is the direct fix.

## Final task-local evidence

- `checks/lesson-census-v2.json`: 300/300 lessons materialized, 1,200 unique
  inputs, 1,200 rotations, zero production or rotation ambiguities.
- `checks/schedule-probe.json`: all six cyclic starts, two seeds, three bands,
  72 four-pair lessons and 288 rotations, zero declared-rival ambiguities;
  minimum two conflict witnesses per lesson.
- `tests/test_generator_8dbffe99308f.py`: authority parity, immutable swap,
  exact controls, malformed/weak input rejection, cyclic lesson coverage,
  arbitrary query rotations, canonical shortcuts, conflict-location diversity,
  canonical profile support, determinism, and the reusable workspace probe.
- `workspace/schedule_probe.py`: source-bound cyclic-start/query-rotation probe
  for future revisions.

## Limits

These checks establish support and identifiability only against the six
explicit executable rivals over the sampled lawful domain. They are not a
proof that no undeclared rule can fit a lesson. The input manifold remains
sparse (4–10 markers) and square (6–10), intentionally matching canonical scale
rather than covering arbitrary dense grids or other sizes.
## Current reviewer considerations

Source SHA-256: `86bd4ad508cefe4d9b0e725a82b1e1ce53a02dded62b8f58a32e83bb8b168f4a`.

# Decisions — 8dbffe99308f

The baseline task notes contained no design rationale, and
`evidence/associated_notes.jsonl` was empty. Therefore baseline intent beyond
the canonical examples and selected Racket program is recorded as unknown; all
choices below are review decisions supported by current-source probes.

## D1 — Preserve the selected Racket authority

**Choice.** Keep the canonical anti-diagonal overlay program unchanged and pin
`RULE_HASH = e248d283a2c2` in the generator.

**Why.** All five canonical pairs match the Python analysis oracle, including
the important immutable-snapshot behavior when two reflected positions are
occupied. The baseline defect was the sampler and missing authority binding,
not the rule.

**Alternatives rejected.** Replacing the Racket program with a one-sided copy or
fill-empty transform would merely encode shortcuts that happen to fit the
canonical examples. Editing the canonical source was unnecessary.

**Probe/failure mode.** Canonical parity and the 120-case Racket rule smoke test
must remain green; any hash drift or Python/Racket mismatch blocks acceptance.

## D2 — Advertise only exact, observable controls

**Choice.** Retain two public axes: square `size` in 6..10 and exact nonzero
`markers` in 4..10. Both are recovered by `observe_overrides`.

**Why.** The baseline metadata described collapsed or unprobed concepts rather
than real controls. Size and marker count are useful, independently testable,
and cover canonical scale.

**Alternatives rejected.** Palette kind, density, position bias, and internal
teaching profile were not exposed because the implementation does not offer
honest independent control over them. The six curriculum profiles remain an
internal deterministic schedule.

**Probe/failure mode.** The final override matrix accepted 4,320/4,320 planned
draws with no errors or findings. Unknown keys and non-integer values are
rejected rather than silently coerced.

## D3 — Use a sparse canonical-scale lawful manifold

**Choice.** Generate 6×6 through 10×10 squares with 4–10 markers, four to six
foreground colors, at least one off-axis marker, and at most one unequal
pre-filled anti-diagonal mirror pair.

**Why.** This covers all canonical exact dimension/palette profiles somewhere
in every difficulty band while keeping individual examples legible. Unequal
occupied partners make snapshot swap semantics observable.

**Alternatives rejected.** A dense arbitrary-grid sampler would increase
surface diversity without necessarily improving rule evidence. Equal-color
occupied pairs were rejected because they do not distinguish overwrite
semantics. Multiple occupied pairs were left outside this bounded training
manifold; see limitations below.

**Probe/failure mode.** `self_check` rejects ragged/non-square grids, nonliteral
ARC colors (including booleans), weak marker/color counts, axis-only scenes,
more than one occupied pair, and equal-color conflicts. Final profile support is
33/60 exact hits and 45/60 in-envelope hits, with support in all bands.

## D4 — Teach both directionality and overwrite semantics

**Choice.** Use six profiles covering above-only, below-only, anti-diagonal fixed
points, and varied unequal occupied-pair conflicts. Conflict coordinates are
sampled across legal orbits rather than anchored to one position.

**Why.** The canonical records place all sources strictly above the
anti-diagonal and leave all reflected partners empty. Consequently both
`above_only` and `fill_empty_only` reproduce every canonical pair. Below-side
sources refute the first; unequal occupied partners refute the second.

**Alternatives rejected.** Merely adding random below-side cells would not teach
immutable-snapshot swapping. Fixing every conflict at `(0,1)` would invite a
coordinate-specific exception.

**Probe/failure mode.** Tests require at least six distinct conflict locations
over the fixed seed set, and the semantic gate verifies 60/60 witness/rival
claims for each canonical shortcut.

## D5 — Alternate ordinary and conflict profiles

**Choice.** Version 3.1.0 alternates non-conflict and conflict profiles, giving
every three consecutive demonstrations at least one conflict and every four
consecutive pairs two conflicts.

**Why.** The first 3.0.0 curriculum looked sufficient in production order but
had only one conflict in some four-pair windows. The large census found 201/1,200
ambiguous rotations: when that sole conflict became the query,
`fill_empty_only` survived all demonstrations.

**Alternatives rejected.** Declaring the curriculum ordered-only would preserve
the weakness and make later dataset reassembly unsafe. Resampling after lesson
construction was also unnecessary because the six-slot schedule can guarantee
the property constructively.

**Probe/failure mode.** The repaired census has 0/1,200 production or rotation
ambiguities. The task-local exhaustive probe covers all six cyclic starts for
two seeds and three bands: 72 lessons, 288 rotations, zero ambiguities, minimum
two conflicts per lesson.

## D6 — Declare executable rivals and witnesses

**Choice.** Include six deterministic competitors (`above_only`, `below_only`,
`fill_empty_only`, reflection-only, main-diagonal, and 180-degree rotation), two
canonical shortcuts, and witnesses linked to the rivals they must refute.

**Why.** Marginal diversity cannot establish that demonstrations determine the
query. Executable rivals turn a vague “looks varied” claim into a reproducible
lesson-level test.

**Alternatives rejected.** A prose-only ambiguity discussion cannot be scored or
regressed. Treating the competitor set as complete was also rejected; finite
rival checks are evidence, not proof of unique induction.

## D7 — Test first and retain failing evidence

**Choice.** Add selected task tests before each behavior change and retain the
RED runs. The final 11 tests cover authority parity, immutable swap, exact
controls, validator rejection, cyclic lesson support, all query rotations,
canonical shortcuts, conflict-location diversity, canonical scale,
determinism,
and the workspace probe itself.

**Why.** The initial tests exposed eight missing behaviors. A later test
specifically requiring every four-window/query rotation failed before the
schedule change, proving that the final rotation guarantee is not a test written
after the implementation.

**Alternatives rejected.** Editing the frozen root fixture was prohibited and
would not give portable source-bound coverage.

## D8 — Build a reusable cyclic schedule probe

**Choice.** Add `workspace/schedule_probe.py`, which imports the selected
source, enumerates cyclic starts, rotates each pair into the query, uses the
actual declared rivals, and reports source hash and finite-scope limitations.

**Why.** The shared census samples many production lessons but does not
exhaustively enumerate a short schedule's starts. The local tool makes that
cheap check repeatable for future agents.

**Failure mode.** The probe cannot detect undeclared plausible rules and is not
a universal identifiability proof. Its report says so explicitly.

## D9 — Keep solve and audit evidence separate

**Choice.** Finish the required blind solve before opening the repair target;
then run a new post-repair solve bound to the final generator hash and mark
prior exposure `yes`. Audit targets were reviewed without edits.

**Why.** This preserves the evidentiary meaning of each episode. The exposed
solve demonstrates that the final generated examples visibly distinguish the
overwrite alternative, but it is not presented as blind model performance.

## Remaining limitations

The generated domain is square, sparse, and permits at most one occupied mirror
pair. A rule that agrees with full overlay on this manifold but mishandles two
or more simultaneous occupied pairs is not refuted. Likewise, the six declared
competitors are useful plausible shortcuts, not an exhaustive hypothesis
class. These limitations are explicit rather than converted into an unsupported
claim of universal identifiability.
