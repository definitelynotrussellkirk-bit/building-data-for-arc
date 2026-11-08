# Working notes: 59ccf6f5cc65

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `62a8a9d56464154cde31ec89c90fb10be582fbc55a70ab0bdaf3a8dea5acf83b`.

# Decisions for `59ccf6f5cc65`

## D1 — Preserve the Racket authority and pin it explicitly

**Choice.** Leave the canonical Racket rule and canonical examples unchanged, add
`RULE_HASH = "bf30289ab720"`, and maintain a pure Python mirror used only for
contracts and tests.

**Rationale.** All five canonical pairs are consistent with exact 4-connected
orange-component membership at a grid corner. The measured defects were in the
input sampler and metadata, not the label rule.

**Alternatives rejected.** Reinterpreting “touching a corner” as touching a border
or having a corner in a bounding box was rejected by the canonical test pair.
Changing the authority merely to match the old rectangular sampler would corrupt
the task rather than repair the curriculum.

**Probe/evidence.** Canonical mirror test, rule smoke, Racket lint, and authority
sync all pass. See `checks/task-tests/result.json` and the final battery summary.

**Failure mode / limitation.** The mirror could share a conceptual bug with the
reviewer; canonical and actual-Racket checks remain the authority.

## D2 — Replace broad unreachable dimensions with four canonical profiles

**Choice.** Sample only `(8,9)`, `(9,10)`, `(8,10)`, and `(9,11)`, one per schedule
slot, with an exact `profile` override.

**Original rationale.** Unknown. The baseline chose 12–16 by difficulty, apparently
for generic visual diversity, but no retained note justified divergence from the
canonical envelope.

**Rationale.** Baseline generated area 144–256 while canonical area centers near
90; exact profile support was 0/60. All four profiles are now reachable by default
and by override.

**Alternatives rejected.** Keeping large grids with a small probability of
canonical draws was rejected because it would preserve a dominant morphology
shortcut. Copying exact canonical scenes was rejected because dimensions can be
matched without memorizing layouts.

**Probe/evidence.** Profile floor reports exact-profile 60/60 and envelope 60/60.
The 128-grid probe reaches all four profiles in every difficulty mode.

**Failure mode / limitation.** This intentionally sacrifices out-of-envelope size
extrapolation; a future broadening should retain a guaranteed canonical fraction
and rerun the semantic census.

## D3 — Restore the exact canonical palette and marker role

**Choice.** Every draw uses background 0, marker 5, and orange 7. Exactly one color-5
singleton occupies a corner and is never transformed.

**Original rationale.** The baseline described a two-color task and omitted color
5 entirely; no retained rationale explained the omission.

**Rationale.** Palette size 3 is part of every canonical input. The marker supplies
a crucial negative: corner occupancy alone is insufficient; the transformed color
must be orange 7.

**Alternatives rejected.** Treating 5 as decorative optional noise was rejected
because a model could learn “any nonzero corner component.” Random extra colors
were rejected as unsupported by canonical evidence.

**Probe/evidence.** Distribution gate passes; `color5_corner_marker` fires 600/600
semantic draws and refutes `any_nonzero_component_at_corner` in all 60 checked
Racket comparisons.

**Failure mode / limitation.** The generator does not teach behavior for other
non-orange colors away from corners because the canonical task does not require it.

## D4 — Assign four corners distinct semantic roles

**Choice.** Rotate a role template around the grid: one marker corner, one
corner-gap decoy, and two candidate true-corner positions. Use one or both true
positions according to `n_corner`.

**Rationale.** Role separation guarantees nonoverlap and makes every scene carry a
positive exact-corner example plus a hard near-corner negative. Rotation removes a
fixed-corner shortcut without rejection sampling.

**Alternatives rejected.** Randomly placing independent objects was rejected
because rare collisions and missing witnesses make exact controls flaky. Always
using the same corner roles was rejected because absolute location would become a
shortcut.

**Probe/evidence.** `layout_rotation` round-trips exactly in 6,030 override draws;
all four values appear in the probe.

**Failure mode / limitation.** The relative cyclic ordering of roles is regular.
The solver does not see `sample_index`, but future randomization could permute roles
while preserving witness guarantees.

## D5 — Make the near-corner negative an L around a missing corner

**Choice.** Paint local cells `(0,1)`, `(1,1)`, `(1,0)` at the decoy corner, leaving
local `(0,0)` zero.

**Rationale.** This single connected component touches both adjoining borders and
has a bounding box containing the grid corner, yet no component cell is the exact
corner. It simultaneously refutes the strongest plausible canonical-demo
shortcuts.

**Alternatives rejected.** A strictly interior negative, which the baseline already
had, cannot distinguish exact-corner membership from broad border/bbox rules. A
single edge-touching object refutes only “any border,” not the stronger two-border
rule.

**Probe/evidence.** The decoy fires 600/600 semantic draws and 128/128 independent
probe draws. The canonical test uses the same logical distinction.

**Failure mode / limitation.** The fixed three-cell L shape is recognizable. Shape
variation could be added later, but only if every variant preserves the exact
missing-corner/two-border property.

## D6 — Guarantee interior negatives, nonrectangular positives, and multi-positive lessons

**Choice.** Place one or two separated interior components by bounded backtracking;
make the first true-corner component a nonrectangular L; schedule `n_corner` as
`1,1,2,2` and `n_interior` as `2,1,2,1`.

**Rationale.** Interior components refute recolor-all-orange. The nonrectangular
positive refutes “solid rectangle at a corner.” A second true corner refutes
“first corner only.” Every three consecutive slots contains a two-corner case.

**Alternatives rejected.** Rectangles only were rejected because they teach shape
rather than component membership. Independent Bernoulli branch sampling was
rejected because complete lessons can omit a necessary branch.

**Probe/evidence.** All six witnesses fire in the four-slot focused test; multiple
true corners fire 287/600 in the semantic census and 64/128 in the independent
probe. All 96 explicitly enumerated cyclic lessons reject every rival.

**Failure mode / limitation.** At most two true and two interior components are
supported. Expanding counts needs a new packing feasibility analysis.

## D7 — Replace dead axes and degenerate textures with four exact controls

**Choice.** Advertise only `profile`, `n_corner`, `n_interior`, and
`layout_rotation`; reject unknown keys, booleans, nonintegers, and out-of-range
values. Set helpful/degenerate texture declarations empty.

**Original rationale.** Baseline metadata listed palette/texture/density controls,
but most were singleton, aliases, ignored, or capable of bypassing invariants.
There was no retained justification.

**Rationale.** Each remaining control changes an observable property and every
joint combination is feasible. This is simpler and more truthful than preserving
nominal breadth.

**Alternatives rejected.** Keeping compatibility aliases was rejected because the
override gate would still treat them as behavioral promises. Declaring numerous
incompatibilities was unnecessary because constructive placement supports the full
Cartesian product.

**Probe/evidence.** Override gate: 67 cases, 3 bands, 6,030 accepted draws, zero
findings and zero incompatibility declarations. Focused tests exhaust 256 boundary
combinations across four difficulty values.

**Failure mode / limitation.** This is an intentional API break from unsupported
baseline pseudo-controls; callers using those invalid keys now receive a clear
error instead of silent behavior.

## D8 — Use constructive bounded placement

**Choice.** Paint corner roles directly and backtrack over finite interior shape/
anchor candidates with one-cell 4-neighbor separation.

**Rationale.** Exact controls need deterministic success on the tightest 8x9
profile. Bounded construction makes failure explicit and keeps global RNG state
untouched.

**Alternatives rejected.** Unbounded random retries were rejected for latency and
flakiness. Falling back to fewer objects would violate exact overrides. Handwriting
a separate layout for all 64 axis combinations would be brittle.

**Probe/evidence.** All 6,030 override draws and 256 focused joint combinations
succeed; deterministic/fresh-return/global-RNG tests pass.

**Failure mode / limitation.** The search is specialized to the current small
shape set and counts. Increasing them without tests may make the tight profiles
infeasible.

## D9 — Declare executable rivals, witness claims, and lesson identifiability

**Choice.** Declare eight rivals and six witnesses, map every witness to the rival(s)
it claims to refute, expose all rivals as lesson competitors, and return reasons
only when a competitor fits all demos but changes the query.

**Rationale.** Witness frequency alone does not establish teaching. Executable
rivals make every claim falsifiable against actual Racket outputs and materialized
lessons.

**Alternatives rejected.** Prose-only `COUNTER_HYPOTHESES` was rejected because no
gate can verify it. A very long speculative rival list was rejected in favor of
compact rules tied to concrete missing branches.

**Probe/evidence.** Semantic gate: 600/600 strict, 6/6 witnesses firing, 6/6 claims
verified, 12/12 lessons identifiable. Extended census: 300 lessons, 1,200 rotations,
zero ambiguity. Independent probe: 96 cyclic lessons, zero survivors.

**Failure mode / limitation.** This finite rival set cannot prove unique human or
model induction. New observed failure modes should become retained executable
rivals with exact counterexamples.

## D10 — Keep `CANONICAL_SHORTCUTS` empty but retain train-fitting rivals

**Choice.** Do not declare the two-border or bbox rule as a canonical shortcut,
because each fails the canonical test pair even though both fit all four canonical
training demonstrations. Keep both in `SEMANTIC_RIVALS` and the reusable report.

**Rationale.** The shared `CANONICAL_SHORTCUTS` contract means “fits every canonical
pair,” not merely demonstrations. Misdeclaring them would make the gate report a
false contract defect.

**Alternatives rejected.** Omitting these rivals entirely was rejected because the
review question and generated teaching quality depend on them.

**Probe/evidence.** `checks/shortcut-probe-final.json` records train-fit `true`,
test-fit `false`, plus exact expected and rival outputs for both names.

**Failure mode / limitation.** A future task split or contract change may warrant a
separate `DEMONSTRATION_SHORTCUTS` hook; currently the workspace probe carries that
analysis.

## D11 — Add independent tests and a reusable declaration-driven probe

**Choice.** Add seven portable focused tests and `workspace/shortcut_probe.py`.
The probe reads actual declarations, computes expected outputs independently,
checks canonical train/test fit, samples all bands, and enumerates schedule starts.

**Rationale.** Tests that only call generator helpers can agree with the same bug.
A reusable artifact lets future agents add a rival and immediately see canonical,
generated, and lesson behavior without reconstructing analysis.

**Alternatives rejected.** Importing private battery internals was rejected by the
packet contract and would make tests fragile. Hard-coding rival names in the probe
was rejected; it consumes `SEMANTIC_RIVALS`, `WITNESS_RIVALS`, and
`LESSON_COMPETITORS` directly.

**Probe/evidence.** Red/green logs retain the missing-hook and missing-tool failures.
The final probe checks 128 generated grids and 96 lessons with no oracle mismatch,
false witness claim, or query-changing survivor.

**Failure mode / limitation.** Its independent oracle is still task-specific. Actual
Racket stages remain required whenever the rule or canonical authority changes.
