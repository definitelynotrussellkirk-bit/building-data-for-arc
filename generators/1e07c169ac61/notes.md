# Working notes: 1e07c169ac61

## Review result

Reviewed imported generator `1.2.0` at SHA-256
`de4e72c6716cd750002b1f3afdf3167eeea84200a6753ed52c4abb679e6bb87e`.
Replaced it with version `2.0.0`, final SHA-256
`e343c884bfc5aed2f048c0c4a9492e70602aaf04e6df004cbee35f505b917174`.
The selected Racket authority was not changed; `RULE_HASH` is pinned to
`b7275e98009a`.

## Lead and reproduced root cause

Prior return `review-938649c4e49e6583:v0001` was used as an unverified lead. It
reported that the baseline fixed the color-9 anchor at the integer grid center,
so a wrong center-pivot rule matched all generated examples, and that the grammar
rejected canonical inputs. The required before battery reproduced those findings:
all three canonical inputs were rejected and five stages failed (`lint`,
`selfcheck`, `defect_lint`, `profile_floor`, `override`).

The baseline also restricted foregrounds to one monochrome connected upper-left
blob. That left color preservation and action on disconnected components
unteachable, and its axis declarations did not provide an honest exact override
contract.

## Implemented design

- Exact axes: `grid_h` 6–10, `grid_w` 6–10, `foreground_size` 3–8, and one of
  four `profile` values.
- Profiles: mono/multicolor × connected/disconnected.
- All generated anchors are off the integer center; every actual-anchor clockwise
  destination remains in bounds; every foreground is changed by the rotation.
- Unknown axes, bad types, bad ranges, bad profiles, and unknown difficulties
  raise instead of falling back.
- `observe_overrides()` reconstructs all exact axis values.
- Canonical-scale profiles `(7,7,3)` and `(6,6,3)` occur deterministically in all
  difficulty bands.
- Four-profile deterministic schedule with `EXAMPLES_NEEDED=4`; every five-pair
  window retains witnesses against all three declared competitors after any one
  pair is held out as query.
- Racket remains the only production label authority. Python helpers in
  `workspace/` are independent analysis/test oracles.

## Verification

- TDD red: 28 failures / 12 passes, retained in `checks/tdd-red/pytest.txt`.
- Final task tests: 40/40 pass in the portable isolated runtime.
- Final battery: 12/12 green, no advisory/failure.
- Official override check: 172 cases / 15,480 draws, no finding or rejection.
- Racket-backed lesson census: 300/300 lessons, 1,500/1,500 query rotations,
  0 ambiguities/errors/warnings, 1,494 unique inputs.
- Task-local cyclic probe: 192 windows / 960 rotations, 0 ambiguities.
- Post-repair visible solve: 4/4 examples on first revision, with earlier exposure
  recorded honestly and no rule source consulted during the solve.

## Limits

The lesson evidence is finite and scores the declared plausible competitors
`center_pivot`, `first_color_only`, and `largest_component_only`. It supports the
actual sampler and arbitrary one-pair query rotations of its five-pair windows;
it does not prove uniqueness against every possible program or model hypothesis.
## Current reviewer considerations

Source SHA-256: `e343c884bfc5aed2f048c0c4a9492e70602aaf04e6df004cbee35f505b917174`.

# Decisions — `1e07c169ac61`

## D1 — Preserve the selected Racket authority

**Choice.** Keep the canonical rule unchanged and pin
`RULE_HASH = "b7275e98009a"` in the generator.

**Original rationale.** The imported generator did not record one. The selected
Racket rule already matched all canonical pairs and passed baseline authority and
rule-smoke stages, so the defect was in the input grammar and contract, not the
transformation.

**Alternatives considered.** Editing the Racket row; implementing labels in
Python; changing the base solution. All were rejected because they would replace
working authority or create a second label source.

**Probe and failure mode.** Baseline and final `authority_sync`, `racket_lint`, and
`rule_smoke` stages were compared. The final 120-draw smoke test has zero crashes,
identity cases, out-of-bounds outputs, or mutations. A future rule change must
update the pin and rerun these source-bound checks.

## D2 — Replace presentation-specific axes with four exact controls

**Choice.** Advertise only `grid_h`, `grid_w`, `foreground_size`, and `profile`.
Each is exact, every declared cross-product is constructive, and
`observe_overrides()` reconstructs all four from pixels.

**Original rationale.** Unknown. The baseline exposed controls that were dead,
ignored, or not observable and silently accepted typoed keys.

**Alternatives considered.** Keep many layout knobs; retain diagnostics-only
axes; allow clamping; retain a generic `texture` string. These were rejected
because they weaken exact replay and make accepted overrides indistinguishable
from fallback behavior.

**Probe and failure mode.** The regression suite tests low/high joint corners in
all bands, bad types, ranges, unknown keys, and reconstruction. The official
final override stage covered 172 cases / 15,480 draws with zero findings. The
domain is intentionally small: dimensions 6–10 and foreground size 3–8.

## D3 — Vary the actual anchor instead of the grid center

**Choice.** Every generated anchor is off the integer grid center, and foreground
sites are chosen only when their actual-anchor clockwise destinations remain in
bounds.

**Original rationale.** The imported generator always placed the color-9 anchor
at `(h//2,w//2)`, making the wrong `center_pivot` rule observationally identical.
The prior return `review-938649c4e49e6583:v0001` identified this as a lead; the
baseline battery and direct canonical checks reproduced it.

**Alternatives considered.** Mix centered and off-center anchors; include one
special witness per lesson; use only canonical anchor locations. Always-off-center
was chosen because every sample then refutes the shortcut and no lesson depends
on one fragile witness.

**Probe and failure mode.** `center_pivot` is a declared semantic rival and is
refuted by every generated pair. The census checked it across 300 lessons and
1,500 query rotations. This does not rule out every alternative pivot hypothesis.

## D4 — Use four semantic profiles

**Choice.** Cycle through mono/multicolor × connected/disconnected foregrounds:
`mono_connected`, `multicolor_connected`, `mono_disconnected`, and
`multicolor_disconnected`.

**Original rationale.** The baseline's single monochrome connected blob made two
canonical-fitting shortcuts plausible: act only on the first color, or only on
the largest component. The selected law instead acts independently on every
nonzero non-9 cell while preserving its color.

**Alternatives considered.** Random colors/connectivity without a schedule;
always multicolor-disconnected; one handcrafted witness profile. Random coverage
could leave a lesson without a needed witness. Always-hard examples reduce
presentation diversity and can teach an accidental composite object prior. The
four simple profiles isolate the semantic factors.

**Probe and failure mode.** `first_color_only` and `largest_component_only` are
executable declared competitors. Multicolor and disconnected witnesses fire in
at least two of every five scheduled pairs. Undeclared rivals remain a limitation.

## D5 — Make the lesson contract robust to any one query rotation

**Choice.** `EXAMPLES_NEEDED=4`; materialize five consecutive pairs from a
period-four schedule and permit any one pair to become the query.

**Original rationale.** The downstream packet explicitly provides an all-query
rotation diagnostic. Correct individual labels do not guarantee that four
remaining demonstrations identify the intended rule.

**Alternatives considered.** Support only the fifth pair as query; randomize the
profile order; add more demonstrations. Ordered-only support is cheaper but less
reusable. Random order complicates replay and can omit witnesses. More demos add
training cost without being necessary for the three declared rivals.

**Probe and failure mode.** `workspace/schedule_probe.py` exhausts every cyclic
start, both retained seeds, three bands, and all five query positions: 192 lessons
and 960 rotations, zero survivors. The Racket-backed census independently checked
300 sampled lessons and 1,500 rotations. This policy is stronger than an exporter
that never rotates its query; that distinction is explicitly documented to avoid
a false rejection of intentionally ordered curricula.

## D6 — Keep canonical-scale support explicit

**Choice.** Schedule exact `(7,7,3)` and `(6,6,3)` profiles in ordinary generation,
while the other two profiles span dimensions 6–10.

**Original rationale.** The baseline rejected all canonical inputs and failed the
per-band profile floor. Purely broad random dimensions could pass only by chance.

**Alternatives considered.** Sample all dimensions uniformly; hard-code only
canonical dimensions. The chosen mixture guarantees floor support while retaining
shape diversity.

**Probe and failure mode.** Final profile-floor hits are 11/20 easy, 9/20 medium,
and 6/20 hard, with 0/3 canonical inputs rejected. This is a support guarantee,
not an attempt to reproduce the exact canonical frequency distribution.

## D7 — Fail invalid calls loudly and diagnose malformed grids

**Choice.** Generation raises on unknown difficulty, unknown axes, wrong types,
out-of-range values, or unsupported profiles. `self_check()` returns diagnostics
rather than raising on malformed grids.

**Original rationale.** Silent fallback made typoed axes appear to work and made
replay claims untrustworthy.

**Alternatives considered.** Ignore unknown controls; clamp values; return a
blank grid. These were rejected because each can silently contaminate data.

**Probe and failure mode.** Task tests cover nine invalid override cases, unknown
difficulty, malformed grids, and canonical acceptance. Future callers relying on
silent fallback will now fail early by design.

## D8 — Keep independent analysis helpers outside label authority

**Choice.** Put geometry, exact observation, competitor implementations, and
cyclic schedule analysis in `workspace/reference_probe.py` and
`workspace/schedule_probe.py`. Racket remains the production label source.

**Original rationale.** The repair needed fast, portable regression tests and an
exhaustive small-schedule probe without importing production transformation
helpers.

**Alternatives considered.** Embed an oracle in `generator.py`; use only manual
inspection; call private runner internals. These were rejected to avoid accidental
label-authority drift and nonportable evidence.

**Probe and failure mode.** The task-test stage relocated tests/workspace into an
isolated runtime and passed 40/40. The Python schedule probe is explicitly marked
non-authoritative; `checks/lesson-census.json` supplies independent Racket-backed
labels.

## D9 — Retain failures and use source-matched resume

**Choice.** Keep the red TDD run, the baseline battery, the mistaken precreated
output launch, and the interrupted first after attempt. Resume only after the
checker validated unchanged source/runtime/settings.

**Original rationale.** A partial or interrupted run is not an aggregate pass,
and removing failed evidence would obscure how the defect was reproduced.

**Alternatives considered.** Delete failed runs or restart under the same output
without validation. Rejected because they weaken provenance.

**Probe and failure mode.** The final aggregate names all 12 stages green and the
same generator SHA used by the census and solve. The first partial after attempt
remains under `checks/after/attempts/0001/`.

## D10 — Stop after finite declared-rival coverage, not claim uniqueness

**Choice.** Report no ambiguity against the declared competitors and explicitly
stop short of universal identifiability claims.

**Original rationale.** Finite rival tests can show that known shortcuts are
refuted but cannot enumerate every rule a model might infer.

**Alternatives considered.** Claim the lesson uniquely determines the rule; add
an unbounded search over programs. Both were rejected as unsupported or
unnecessary for this review.

**Limit.** The evidence covers the actual sampler, three declared competitors,
three difficulty bands, 300 Racket-labelled lessons, all 1,500 query rotations,
and an exhaustive small cyclic-start probe. Other rivals remain unknown.

## Current bounded audit assessment

`review-a57718d771ccb867:v0001` found no actionable in-domain defect on source `e343c884bfc5aed2f048c0c4a9492e70602aaf04e6df004cbee35f505b917174`. This is reviewer-reported evidence for the tested examples and controls only. The current assessment and minimal receipts are in `evidence/current-audit-assessment.json`; its domain limits remain relevant.
