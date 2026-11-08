# Working notes: 0bb8813a21dc

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `d5dd2a47823902143f0792e70e7a4e11772d4a429b388d1b8ba667ab471b87c0`.

# DECISIONS — 0bb8813a21dc

## Context and prior lead

The immutable selected baseline was generator v2.2.0 at SHA
`fe138096bad20d52d51c27339f43fd09299984af181fa2568646ecaca8b2bf28`.
I used prior return `review-7f2d5f89f41a5efa:v0001` only as a lead: it alleged
override/metadata defects against these same bytes. I independently reran the
full baseline battery before treating any allegation as measured fact. That run
confirmed the missing rule pin, dead texture values, invalid ordinary-domain
degenerates, zero canonical-profile support, absent semantic contract, and
14,989 override findings.

## D1 — Preserve the Racket authority

**Choice.** Keep the canonical/base Racket program unchanged and pin
`RULE_HASH = "42a14ef4873c"` in the generator.

**Rationale.** Authority sync and rule smoke showed the selected program already
solved all four canonical pairs. The defects were in generated inputs and
metadata, not labels.

**Alternatives rejected.** Rewriting or broadening the rule would create needless
label drift and make the repair harder to accept.

**Probe.** Final authority sync and 120-call rule smoke with Python-mirror parity.

**Limitation.** The Python mirror is only a fast task-local oracle; the Racket
source remains authoritative.

## D2 — Replace the broad override surface with one exact observable axis

**Choice.** Remove `grid_h`, `grid_w`, `palette_kind`, `row_count`, and the mixed
helpful/degenerate `texture` domain. Expose only
`scene_profile = identity_scope | mixed_scope`, validate its type/value, reject
unknown keys, and recover it from pixels with `observe_overrides`.

**Rationale.** A control is useful only when a caller can request it exactly and
verify it in the returned grid. The baseline’s palette-kind values were
byte-identical, difficulty-local ranges contradicted declared ranges, and
negative fixtures were advertised as ordinary valid values.

**Alternatives rejected.** Keeping aliases for backward compatibility would
preserve silent behavior and multiply incompatible combinations. Declaring all
combinations incompatible would make the API technically legal but practically
misleading.

**Failure modes checked.** Unknown key, non-string/unknown profile, exact value
honoring in all bands/seeds, deterministic replay, and observed profile equality.

## D3 — Use exact canonical shape/palette support

**Choice.** Cycle these four canonical profiles in every band:
`(5,6,9)`, `(4,7,10)`, `(4,6,8)`, and `(4,7,8)`, where the third value includes
background.

**Rationale.** The baseline had 0/60 exact and 0/60 envelope hits. All four
canonical inputs are valid and small enough that constructive exact support costs
nothing. Cycling, rather than probabilistic anchoring, guarantees coverage in any
20-draw profile-floor sample.

**Alternatives rejected.** A broad 6–9 by 7–11 domain preserved morphological
drift. Rejection sampling could hide impossible combinations and weaken replay.
A 5% anchor branch would pass the floor but make short lessons less reliable.

**Probe.** Task test requires all four profiles in 20 draws per band; final gate
records 60/60 exact hits.

**Limitation.** The curriculum does not teach arbitrary canvas sizes. That is
intentional because the selected authority is generic but the demonstrated
training family is small and exact.

## D4 — Construct three semantic row roles

**Choice.** Every input has exactly three active rows. One sparse witness uses
`[leader, modal, modal, rightmost]` across a background gap. Another row repeats
the true leader while retaining a singleton nonleader. The third carries the
remaining palette; `identity_scope` instead makes one row already uniform.
Roles and row positions are shuffled deterministically.

**Rationale.** The sparse row simultaneously distinguishes leftmost from
rightmost, modal, span-fill, row-fill, and per-component behavior. Repeating the
leader while leaving a singleton makes “choose the rarest color” wrong. Different
row leaders reject a global-color rule. The uniform profile retains positive
identity behavior without allowing an all-identity lesson.

**Alternatives rejected.** Fully random row colors allowed accidental shortcut
agreement. Single-cell, empty, and all-same-color degenerates supplied no teaching
contrast. Making every row mixed would omit the lawful already-correct case.

**Failure modes checked.** At least three occupied cells per active row, visible
nonleader color, at least two row leaders, at least one internal gap, strict
palette range, and profile observer consistency.

## D5 — Alternate two lesson profiles deterministically

**Choice.** `schedule_profile` alternates `identity_scope` and `mixed_scope` by
sample index; difficulty phase-shifts only the canonical shape/palette cycle.

**Rationale.** Any three-demo lesson sees both identity and changed behavior,
while every input independently carries all decisive rival counterexamples. The
schedule is transparent and exhaustive cyclic-window testing is cheap.

**Alternatives rejected.** Seed-random profile choice permits unlucky homogeneous
lessons. Encoding complexity by removing witnesses in easy examples would make
some query rotations underdetermined.

**Limitation.** Difficulty bands vary surface profile phase, not semantic rule
complexity. This is deliberate: training quality was prioritized over artificial
band separation.

## D6 — Make semantic alternatives executable

**Choice.** Declare and execute seven rivals: rightmost color, modal color,
rarest color, global first color, fill between extremes, fill the active row, and
recolor each contiguous component separately. Pair every witness with at least
one named rival and require `lesson_identifiable` to reject all rivals on the
demonstrations.

**Rationale.** Feature-presence prose does not establish that a lesson teaches the
intended mapping. Executable alternatives turn ambiguity into a reproducible
counterexample.

**Alternatives rejected.** The first repair included an “identity row present”
witness without a rival. The strict gate correctly rejected it as weak; I removed
it from the witness contract instead of inventing an artificial competitor.

**Limitation.** Seven rivals are finite evidence, not a proof of unique induction.
The self-review finding demonstrates why undeclared-rival discovery should become
a shared gate.

## D7 — Treat rarest-color as a canonical shortcut

**Choice.** Add `rarest_row_color` to `CANONICAL_SHORTCUTS`, semantic rivals, and
lesson competitors; require it to fit every canonical pair and to fail every
generated input.

**Rationale.** It is a particularly dangerous hypothesis because it agrees with
all four canonical labelled examples. The first repaired draft omitted it; a
fresh self-review caught that omission before handoff.

**Probe.** A test first failed on the missing declaration, then passed after the
anti-rarest construction. The final production census records the shortcut as
refuted on every lesson and every query rotation.

## D8 — Keep validators narrow and literal

**Choice.** `self_check` validates the actual training grammar; `strict_canonical_like`
adds exact shape/palette membership. Cell validation rejects bools, non-integers,
out-of-range colors, ragged grids, and empty grids.

**Rationale.** The baseline’s claimed domain exceeded what its own generator and
difficulty branches honored. A narrow truthful contract is more useful than a
broad nominal one.

**Alternatives rejected.** Relaxing `self_check` to accept negative fixtures would
make gate success meaningless. Conflating task grammar with exact canonical
profiles would make generalized future probes impossible.

## D9 — Add a source-bound lesson-window probe

**Choice.** Build `workspace/lesson_probe.py` and tests. It imports the generator
by path, derives rivals from declarations, checks deterministic generation,
validators, every four-pair sliding window, every held-out-query rotation, and
retains exact failures with source hashes.

**Rationale.** The standard semantic gate samples only a small number of lessons;
the production census uses independently materialized lessons. The task’s small
period makes exhaustive overlapping windows cheap and catches schedule boundary
errors.

**Alternatives rejected.** Hard-coding rival names would silently go stale. Using
the private Racket runner in the workspace would make it nonportable; the probe
uses the mirror and relies on separate parity checks.

**Limitation.** The helper tests declared rivals only and uses source-bound mirror
labels. It complements, rather than replaces, authority smoke and production
census.

## D10 — Keep audit targets findings-only

`c29d882947ce` and `e04777b1f6d7` were independently assigned audit targets. I
retained compact evidence and made no changes outside the selected task. The
first is a reproduced shortcut/teaching defect. The second is intentionally
classified as a suspected coverage gap rather than a label error because the
battery is green and the finite sample cannot establish intended domain policy.

## Stopping decision

I stopped after the final source passed the full battery, focused tests, two
large lesson checks, source-bound solve, and fresh-packet patch replay; a second
self-review found no new concrete shortcut among the tested families. Remaining
uncertainty is explicitly bounded: finite rival sets do not prove universal
identifiability, and the curriculum intentionally stays within canonical
shape/palette profiles and three active rows.
