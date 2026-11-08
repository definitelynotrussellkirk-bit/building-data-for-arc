# Working notes: 8dd23f285c61

## Baseline read

The selected baseline was generator SHA-256
`dda9edbee405ca1e08e75b89d14f8885240ec7bb6418d7bbac7cfe1f014010ee`.
No prior associated-return note was present; `evidence/associated_notes.jsonl`
was empty. `SUMMARY.md` and the source itself were therefore the only imported
leads, and all claims below were remeasured against the pinned baseline.

The completed before battery retained under `checks/before-complete/` failed
three stages: lint (missing `RULE_HASH` plus collapsed axes), defect lint (dead
and overlapping texture controls plus a lawful-looking degenerate), and the
override contract (unknown keys accepted and many undeclared multi-axis
rejections). Rule smoke, authority sync, self-check, profile floor, diversity,
grammar, and Racket lint passed. The baseline semantic gate was advisory because
there was no executable semantic contract.

## Root cause and design

The generator's apparent nine-axis surface mostly did not control pixels. Its
actual distribution was one full-height vertical wall, one short horizontal
wall to its right, and 2..3 emitters. This fixed template left a strong
canonical-compatible rival untested: one- and two-cell gray components could be
ignored as noise because no public demonstration required a tiny wall to stop a
ray.

Version `3.0.0` replaces that template with a constructive sampler. It exposes
only four exact, observable controls (`grid_h`, `grid_w`, `n_seeds`, and
`n_wall_components`), rejects unknown/non-integer requests, varies 1..4
disconnected wall components and 2..5 emitters, and places a guaranteed tiny
wall blocker with an unmasked cell behind it. Longer barriers preserve canonical
morphology. The canonical Racket authority was not changed.

## Independent tooling

`workspace/reference_probe.py` implements a task-local geometry oracle without
importing generator helpers. It dynamically executes every declared canonical
shortcut and lesson competitor, checks every cyclic lesson start, records exact
axis/distribution counts, and can compare canonical, hand-written, and generated
inputs to `Catalog.apply`. The focused tests bind the generator to that tool and
include real Racket parity.

## After-battery performance repair

The first after battery, bound to generator SHA-256
`dfa79118b66af7a56056883744a6ea169ab5d51dddb200a463a85e8e96cc4531`,
finished 11/12 stages green but the exhaustive override stage timed out after
302 seconds. That failed run is preserved under
`checks/after-timeout-dfa79118/`.

A cProfile run over 200 maximal 16x16 draws took 10.020 seconds and assigned
5.718 seconds to rebuilding component candidates and 3.568 seconds to enumerating
teaching layouts. The root cause was recomputation of geometry that depends only
on canvas shape/direction, repeated tens of thousands of times by the 269-case
override matrix.

The final implementation caches immutable wall templates by shape and caches
compact teaching seed/distance bounds, materializing only the selected teaching
ray. A regression first failed because the cache APIs were absent, then passed.
A 2,000-draw direct benchmark measured 1.200 ms/default draw and 2.177 ms/maximal
exact draw; the final focused suite remained green.
## Current reviewer considerations

Source SHA-256: `da36673a235091edcc9dc1937da280c3d9edbf6c8ac6c2fa30d447bc89e71a9e`.

# Decisions — 8dd23f285c61

The selected baseline was SHA-256
`dda9edbee405ca1e08e75b89d14f8885240ec7bb6418d7bbac7cfe1f014010ee`.
Its imported associated-notes ledger was empty, so the original rationale below
is marked unknown where the source did not explain it. Measurements refer to the
retained before/after evidence, not to prior review claims.

## D1 — Replace the fixed two-wall template rather than patch its cosmetics

**Baseline choice and rationale.** Version `2.0.1` always drew one full-height
vertical wall and one short horizontal wall on its right. The original rationale
was not recorded; `SUMMARY.md` simply restated that template.

**Decision.** Version `3.0.0` constructs 1..4 disconnected wall components. One
component is a one- or two-cell teaching blocker, while the others are varied
horizontal/vertical segments with isolated-cell fallbacks only when necessary.

**Why.** The baseline's apparent texture/palette controls did not change pixels,
and its fixed geometry never made a tiny wall semantically relevant. That leaves
the exact rival “components of size at most two are noise and do not stop rays”
consistent with all five canonical pairs. The new construction makes that rival
wrong on every ordinary draw while retaining longer canonical-looking barriers.

**Rejected alternatives.** Merely randomizing the old wall coordinates would
leave the rival untouched. Keeping a single full-span wall plus decorative noise
would vary appearance but not the teaching evidence. Rejection sampling was also
rejected: the requested boundary combinations are small enough to construct
directly and exact controls should not fail probabilistically.

**Failure mode / limitation.** Guaranteeing a tiny blocker in every draw
intentionally overweights this ambiguity relative to the public examples. It is
a curriculum choice, not a claim that real ARC inputs always contain tiny walls.
Longer wall orientation and placement still vary, but not every extra wall is
guaranteed to intersect an emitter ray.

## D2 — Expose only four exact, pixel-observable axes

**Baseline choice and rationale.** The source advertised nine axes, including
`palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`,
and `texture`. Several were singleton domains; helpful texture values overlapped
without affecting output. The original rationale was unknown.

**Decision.** Advertise exactly `grid_h`, `grid_w`, `n_seeds`, and
`n_wall_components`. `observe_overrides()` recovers all four from returned
pixels. Unknown keys, booleans, floats, and out-of-domain values are rejected.
There are no incompatible combinations in the stated domains.

**Why.** A small honest interface is stronger than a large decorative one. The
completed baseline override gate found an accepted unknown key and thousands of
undeclared multi-axis rejections. The repaired matrix has no inert or silently
clamped axis.

**Rejected alternatives.** Marking dead axes “diagnostic” would make the checker
quiet without giving callers useful control. Retaining degenerate textures would
mix malformed/ambiguous cases into an ordinary training generator; explicit
negative-test fixtures are better for those cases.

**Failure mode / limitation.** The new interface is intentionally incompatible
with callers that relied on the old nonfunctional texture names. That break is
preferable to preserving false contracts.

## D3 — Domain bounds: height 7..16, width 9..16

**Decision.** Heights cover 7..16 and widths 9..16, with canonical sizes
weighted rather than hard-coded. All five canonical inputs are accepted.

**Why.** Canonical examples occupy heights 7..10 and widths 10..12. The larger
range supplies scale variation while width 9 leaves enough room for an emitter,
a separated blocker, an observable cell behind it, and multiple disconnected
components even at the hardest exact boundary.

**Rejected alternatives.** The baseline declaration allowed widths 7 and 8,
but the fixed implementation could not honor many declared combinations. A
7..16 width range could be made possible with more special cases, but it adds
edge-layout complexity without canonical evidence or a clear teaching benefit.

**Failure mode / limitation.** The Racket rule itself can operate on narrower or
larger rectangular grids; this sampler deliberately covers a documented subset,
not the full mathematical input universe.

## D4 — Emitters 2..5 and wall components 1..4

**Decision.** `n_seeds` is 2..5 and `n_wall_components` is 1..4. Difficulty only
changes curriculum weighting: easy favors 2 emitters/2 walls, medium 3/3, hard
5/4. Overrides remain exact in every band.

**Why.** Canonical inputs use two emitters and one to three wall components.
The extended counts create overlap and ray interactions without crowding the
smallest 7x9 grid. Four components also exercises disconnected-component logic.

**Rejected alternatives.** Single-emitter defaults make accidental one-object
heuristics easier; six emitters add clutter without public support. A raw
wall-cell-count axis was rejected because geometry and connectivity are the
semantically important observable.

**Failure mode / limitation.** The generator does not teach a one-emitter case,
and additional emitters are preferentially placed in interior cells. Those are
lawful under the rule but outside this curriculum slice.

## D5 — Preserve the tiny-wall disagreement after adding other emitters

**Decision.** The primary emitter, blocker, and first cell behind the blocker are
selected together. Extra walls cannot occupy that protected ray. Extra emitters
cannot share the rival cell's row or column, preventing them from painting the
same cell under both rules and hiding the disagreement.

**Probe.** `SEMANTIC_WITNESSES["tiny_wall_blocks"]` compares the intended mirror
with the named rival. The focused regression samples 160 draws per band and
requires the witness in every draw. The larger independent probe repeats this
with its own oracle and all cyclic lesson starts.

**Rejected alternative.** Checking only that a tiny component exists is
insufficient: another emitter can make both candidate rules produce the same
final grid. The construction therefore protects an actual output disagreement,
not metadata.

**Failure mode / limitation.** The witness guarantees at least one discriminating
cell; it does not maximize disagreement area or guarantee every wall matters.

## D6 — Strict validation remains broader than generated teaching cases

**Decision.** `strict_canonical_like()`/`self_check()` validate shape, literal
integer cells, colors 0/2/5, 2..5 emitters, and 1..4 wall components. They do not
require the tiny-wall witness. `generate()` separately asserts the teaching
invariant.

**Why.** A validator that required the new witness would incorrectly reject the
canonical demonstrations it is supposed to support. Domain validity and lesson
quality are distinct contracts.

**Rejected alternative.** Making `self_check()` accept declared degenerates based
on `meta` was the baseline behavior and allowed structurally bad cases to pass.
The repaired validator judges pixels, not a caller's label.

**Failure mode / limitation.** Some unusual but lawful arrangements pass
`self_check()` even though this sampler never emits them. That is intentional;
`self_check()` is not a provenance test.

## D7 — Add an executable semantic contract and one explicit competitor

**Decision.** Declare `tiny_wall_blocks`, `ignore_tiny_walls`, their witness-rival
mapping, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and
`lesson_identifiable()`. Require three demonstrations per lesson.

**Why.** The baseline semantic gate was advisory because it could not test what
the generator was meant to teach. The named competitor fits every canonical
pair but is falsified by generated lessons. Three examples retain varied
orientations/counts while every individual generated input already contains the
essential witness.

**Rejected alternatives.** A prose-only statement is not falsifiable. Declaring
many speculative rivals was also rejected; each declared rival should be both
plausible and independently testable.

**Failure mode / limitation.** Passing this finite competitor set does not prove
unique induction of the intended rule. Other contrived rules can fit any finite
sample; reports therefore say “identifiable against declared competitors,” not
universally identifiable.

## D8 — Keep Python mirrors test-local in authority status

**Decision.** The generator's small mirror exists only to execute semantic
witnesses/rivals. `workspace/reference_probe.py` supplies a separately written
oracle, and its optional Racket path uses the public `Catalog.apply` API. The
canonical Racket authority remains the label source.

**Why.** A Python mirror can share a bug with a generator if treated as truth.
Independent implementation plus real-Racket parity catches that class of error.

**Failure mode / limitation.** The independent oracle and generator mirror still
encode the same written interpretation. The Racket comparison is the final
cross-language check, but it samples rather than exhausts every possible grid.

## D9 — Pin the rule hash; do not alter the Racket authority

**Decision.** Pin `RULE_HASH = "346b3beb0ce3"`. No Racket source or canonical
example changed.

**Why.** Canonical outputs, the independent oracle, and Racket execution agree.
The defect was generator coverage and contracts, not the transform.

## D10 — Build reusable source-bound probes and tests

**Decision.** Add `workspace/reference_probe.py` and a 40-test task-local suite.
The probe discovers declarations dynamically, checks all canonical shortcut
claims, measures unique inputs and axis ranges per band, runs every cyclic lesson
start, emits a hash-bound JSON report, and can verify Racket parity.

**Why.** The shared battery's lesson sample is intentionally small. A task-local
probe makes the review's stronger claim reproducible and gives future agents a
single command rather than prose instructions.

**Failure mode / limitation.** The probe is task-specific and assumes this
three-color ray vocabulary. It is reusable for future revisions of this task,
not a generic ARC semantic checker.

## D11 — Cache static geometry after the exhaustive matrix exposed a timeout

**Observed failure.** The first repaired source passed 11/12 battery stages but
its override stage was killed at 302 seconds. The failure is retained at
`checks/after-timeout-dfa79118/` and is bound to source hash
`dfa79118b66af7a56056883744a6ea169ab5d51dddb200a463a85e8e96cc4531`.

**Root cause.** Profiling 200 maximal draws took 10.020 seconds: 5.718 seconds
were spent rebuilding every possible line-segment component, and 3.568 seconds
were spent enumerating/materializing every possible teaching ray. Those objects
are static for a given shape/direction but were rebuilt on every call.

**Decision.** Cache wall templates by `(height, width)`. Cache only compact
teaching seed/distance bounds by `(height, width, direction, tiny_size)`, then
materialize the one selected path. The caches are unbounded over finite declared
domains (80 shapes and at most 640 teaching keys), which prevents LRU thrashing
inside the 269-case override matrix.

**Verification.** A cache regression was written and observed failing before the
implementation. Afterward, 2,000 default draws measured 1.200 ms/draw and 2,000
maximal exact draws measured 2.177 ms/draw; all 41 focused tests remained green.

**Alternative rejected.** Increasing the shared stage timeout would conceal a
sampler inefficiency and slow every downstream consumer. A randomized rejection
loop would be faster in common cases but weaken exact override guarantees.

**Failure mode / limitation.** Warming all declared shapes uses additional
process memory (about 216 MiB peak in the benchmark process). The domain is
finite and the trade is intentional; a future expansion of dimension ranges
should revisit cache bounds or use compact coordinate templates.
