# Working notes: 946e33609350

## Current rule and authority

The intended transformation is **fill by nearest seed through corridors**.
Color `1` is an impassable wall. Every other non-zero value is a distinct
singleton seed. A zero cell receives the color of its unique nearest seed by
four-neighbor shortest-path distance through non-wall cells. A finite tie stays
`0`; walls and seeds are unchanged. The selected canonical rule is pinned by
`RULE_HASH = "1ec8459f97ec"`. No Racket source was changed in this review.

## Reversed baseline decision

The pinned baseline generator (`e3ba8fd25c192c9abdf6a268ca0164c9e73193759a4313c78dd47244e3b57aad`)
implemented an unrelated vertical gallery of colored motifs. Generic shape and
execution checks could pass even though generated inputs did not teach or even
represent this task. The before battery recorded 7 green, 2 advisory, and 3
failed stages; lint lacked a rule pin, override declarations were not truthful,
the canonical-profile floor was 0/60, and no executable semantic contract was
present.

The new choice is a source-bound framed-corridor generator rather than a patch
to the motif gallery. The final generator SHA-256 is
`565b51fe9ad3fa0cf9f13cb44bb5a534a035319232b45e9ca5dc76f769c63537`.
No prior selected-task return was treated as current-source evidence; the pinned
baseline, canonical examples, and before battery were the repair inputs.

## Distribution decisions

- Every lawful grid has a complete color-1 boundary frame, two or three distinct
  singleton seed colors, and either no interior wall or one horizontal/vertical
  barrier with one open gate.
- The default cyclic schedule is `horizontal_gate`, `open_tie`,
  `vertical_gate`. Any three consecutive demonstrations therefore include a
  wall detour in each orientation and an explicit finite tie.
- Default dimensions and seed counts use the measured canonical profiles:
  `8x9/3`, `6x9/2`, and `8x10/3`. This keeps every lesson source-shaped while
  still allowing exact public overrides over height `6..10`, width `9..12`,
  seed count `2..3`, and profile.
- Difficulty is deliberately a deterministic symmetry shift, not a change to
  the law or to advertised axis support. This keeps the knob observable without
  hiding a separate grammar behind each band.
- Unknown overrides and malformed values are rejected. The full Cartesian
  product of declared exact axes is constructively supported; no incompatibility
  exceptions are declared.

Rejected alternatives were random maze walls (larger but harder to validate and
more shortcut-prone), random independent examples without a semantic schedule
(could omit a tie or wall detour), and an ordered-only lesson claim (downstream
query rotations are supported and were tested explicitly).

## Semantic contract and reusable probe

`rule_mirror` is a pure-Python authoring mirror of the selected law. Three named
rivals are executable: break finite ties by lowest color, ignore walls and use
Manhattan distance, and ignore the numerically highest seed. Matching witnesses
ensure the lesson contains a refutation of each rival. `lesson_identifiable`
rejects a lesson when a declared rival fits every demonstration but changes the
query.

`workspace/lesson_probe.py` loads the adjacent generator by exact path, records
its SHA-256, checks all cyclic schedule starts in a requested finite sample,
scores every declared rival, and checks every query rotation. It is intentionally
lightweight and does not replace the Racket-backed semantic gate or census.

## Verification on final bytes

- Task-local tests: 28 passed in the isolated task-test stage.
- Full battery: 12/12 stages green.
- Hard semantic gate with required query rotations: passed.
- Racket-backed census: 300/300 ordered lessons and 1,200/1,200 query rotations
  identifiable against declared rivals; 868 unique inputs; no materialization,
  scoring, or hook errors.
- Fast cyclic probe: 100 ordered lessons, 400 query rotations, 340 unique inputs,
  and zero surviving declared rivals.
- Fresh visible-only post-repair solve: first implementation passed all three
  visible demonstrations; earlier rule exposure was declared honestly.

Evidence is under `checks/after-battery/`, `checks/task-tests-final/`,
`checks/required-rotations-final/`, `checks/lesson-census.json`, and
`checks/lesson-probe.json` in the review packet.

## Known limits and open status

The grammar intentionally covers framed corridor instances with at most one
one-gap barrier and two or three seeds; it does not attempt arbitrary mazes,
multiple disconnected chambers, or more seed colors. The finite declared-rival
checks do not prove universal identifiability against every possible hypothesis.
The Python mirror is test tooling, not label authority. Catalog approval remains
false and training safety remains unverified until maintainer intake; generator
review also does not admit model trajectories to training.
## Current reviewer considerations

Source SHA-256: `565b51fe9ad3fa0cf9f13cb44bb5a534a035319232b45e9ca5dc76f769c63537`.

# Decisions for 946e33609350

## D1 — Replace the baseline instead of incrementally patching it

**Prior choice.** The baseline generated a vertical gallery from disconnected
colored motifs. Its original rationale is unknown; it did not correspond to the
selected canonical task.

**New choice.** Replace the implementation with a generator whose pixels,
validator, rule mirror, semantic witnesses, and lesson policy all describe
nearest-seed propagation through walls.

**Reason/evidence.** This was an authority/source-binding defect, not a local
sampling bug. The before battery's generic green stages did not make the motif
gallery relevant. `checks/before/checks/946e33609350_before_battery_summary.json`
and the canonical title/rule hash establish the mismatch.

**Rejected alternative.** Retain motif generation and merely add `RULE_HASH` or
repair axes. That would make contracts cleaner while still teaching the wrong
transformation.

## D2 — Use a framed corridor grammar with one optional one-gap barrier

**Choice.** A lawful input has a complete color-1 boundary frame, two or three
distinct singleton seeds, and either no interior wall, one horizontal barrier,
or one vertical barrier. All non-wall cells remain seed-reachable.

**Reason/evidence.** This grammar is close to all three canonical profiles,
constructively valid, easy to recover from pixels, and sufficient to expose the
essential geodesic-vs-Manhattan distinction. Canonical inputs pass `self_check`,
and the final profile-floor stage passes independently in every band.

**Rejected alternative.** Arbitrary random mazes would increase topology count
but complicate override observability, reachability, and semantic-witness
coverage. Multiple disconnected chambers could also turn “unreachable remains
zero” into an unintended lesson branch.

**Failure mode/limit.** The production distribution does not cover arbitrary
maze topology, multiple barriers, or disconnected open regions.

## D3 — Advertise only exact, pixel-observable axes

**Choice.** The public axes are `grid_h` (`6..10`), `grid_w` (`9..12`),
`n_seeds` (`2..3`), and `profile` (three named values). Every Cartesian product
is supported in every difficulty band. Unknown keys and malformed values raise.

**Reason/evidence.** The baseline's singleton/dead axes and swallowed unknown
keys made override reports unreliable. The final override matrix is green, and
`observe_overrides` reconstructs every public value from the returned grid.

**Rejected alternative.** Preserve compatibility aliases such as palette size,
density, or position bias. They had no independent observable effect and would
reintroduce fake degrees of freedom.

## D4 — Make difficulty live through symmetry, not through a different law

**Choice.** Difficulty deterministically shifts among identity, left-right,
up-down, and combined flips while the profile, dimensions, seed count, and rule
remain unchanged.

**Reason/evidence.** The harness expects a live difficulty knob, but this task's
semantic complexity comes from ties and barriers rather than larger grids alone.
Symmetry produces visibly different valid samples without changing the supported
axis product. Focused tests verify at least two band outputs over sampled seeds
and verify no global random-state mutation.

**Limit.** Difficulty is distributional variety, not a calibrated model-hardness
ranking.

## D5 — Require three ordered demonstrations and support arbitrary query rotation

**Choice.** `EXAMPLES_NEEDED = 3`, with a cyclic schedule of
`horizontal_gate`, `open_tie`, and `vertical_gate`. Production uses those three
ordered demonstrations followed by one query. Because downstream assembly may
rotate the query, every hold-one-out position is also required to remain
identifiable against declared rivals.

**Reason/evidence.** One profile alone can omit a core branch. Any three
consecutive schedule positions contain all profiles. The hard semantic gate
passes, the Racket-backed census passes 300 ordered lessons and all 1,200 query
rotations, and the fast probe checks 100 cyclic starts plus 400 rotations.

**Rejected alternative.** Claim only the native ordered query policy. It would
be cheaper, but the generator already supports rotations and testing them avoids
the exact kind of curriculum hole found in audit target `bb435f29015f`.

**Limit.** Passing finite rotations against named rivals is not a proof of unique
rule induction.

## D6 — Encode task-linked witnesses and plausible competitors

**Choice.** The witnesses are: a finite tie remains zero, a wall changes nearest
seed relative to Manhattan distance, and all three seed colors win at least one
additional cell. Their corresponding competitors break ties by lowest color,
ignore walls, and drop the numerically highest seed.

**Reason/evidence.** These are simple, executable shortcuts that can label many
individual grids correctly while implementing the wrong concept. They directly
exercise tie handling, wall semantics, and color-rank/unused-seed shortcuts.
Every final lesson refutes every declared competitor in the tested samples.

**Rejected alternative.** Rely on correct labels or morphology alone. Correct
labels do not establish that demonstrations disambiguate a plausible wrong
rule.

**Limit.** The competitor set is finite and authored; undeclared shortcuts can
remain.

## D7 — Keep a Python rule mirror and add a source-hashed fast probe

**Choice.** `rule_mirror` supports validator/tests and
`workspace/lesson_probe.py` checks the deterministic schedule quickly. The probe
loads the adjacent source by exact path and records its SHA-256.

**Reason/evidence.** This gives future agents a fast feedback loop for cyclic
starts and rotations without paying for a full Racket-backed census after every
small change. A focused test binds the tool to the production generator.

**Rejected alternative.** Treat the mirror as label authority. The selected
Racket program remains authoritative; final parity and census claims use public
Racket-backed commands.

**Limit.** The probe covers only declared competitors and a finite requested
sample.

## D8 — Do not change the Racket authority

**Choice.** Keep canonical rule bytes unchanged.

**Reason/evidence.** Rule smoke, authority synchronization, canonical examples,
and the Python mirror all agree. The defect was entirely in generator selection
and teaching distribution. Changing the rule would add risk without fixing the
actual cause.

## D9 — Preserve review/admission boundaries

**Choice.** Report final checks as green but leave catalog approval and training
admission untouched.

**Reason/evidence.** The packet's catalog provenance remains `approved: false`
and `train_safety: unverified`. Generator correctness and lesson diagnostics do
not admit model trajectories or independently alter maintainer safety state.

## D10 — Audit findings remain audit-only

**Choice.** Reproduce and report defects in `7768dfc99e25` and
`bb435f29015f` without editing either source.

**Reason/evidence.** The assignment authorizes edits only to the selected task.
Exact current hashes, Racket receipts, validator status, and counterexamples are
retained under `checks/audit/` and summarized in `AUDIT.md`.
