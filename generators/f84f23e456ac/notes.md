# Working notes: f84f23e456ac

## 2026-10-04 review `review-007015136a51e0e4`

The selected baseline was the packet-pinned generator SHA-256
`4f7392e2f9acb72f77adb7f0e698a36870650bb17e5aee494395947e4e14bede`.
No prior return was used as evidence; the empty associated-notes file supplied
no lead.  The canonical Racket authority was not changed.

### Reproduced baseline defects

- `RULE_HASH`, structural `self_check`, and a semantic lesson contract were
  absent.
- Advertised texture/palette controls overlapped or were unobservable; global
  axis endpoints were rejected in some difficulty bands; unknown controls were
  silently ignored.
- Random support could make the observed nonzero bounding box disagree with the
  requested motif dimensions.
- All five canonical motifs have width three, so the executable
  `fixed_motif_width_3` rival fits every canonical pair.
- The baseline battery finished with 6 green stages, 1 advisory stage, and 5
  failed stages; see `checks/before/`.

### Final design

The generator now pins rule hash `54458840a785`, validates a primitive
origin-cropped motif, exposes six exact observable axes, and rejects unknown
controls.  Ordinary generation uses a complete 15-slot profile cycle containing
all five canonical size/palette profiles plus minimum/maximum canvas sentinels;
the profile phase rotates with the seed.  The motif support is sampled within an
exact sparse/dense class while opposite boundary anchors and rejection of
smaller periods keep the requested bounding box and primitive period truthful.

The three-pair lesson schedule varies motif width and includes executable rivals
for identity, horizontal-only tiling, vertical-only tiling, and fixed width
three.  `lesson_identifiable` rejects a lesson only when a declared rival fits
all demonstrations and differs on the query.  `workspace/probe_curriculum.py`
checks canonical-shortcut fit, sampler support, rival refutation, and every
requested cyclic start; it is intentionally not an authority substitute.

### Rejected alternatives

- A fixed L-shaped zero guard passed correctness gates but produced only
  179/300 distinct production-shaped easy-band inputs.  Randomized bounded
  supports raised the final cohort to 288/300 easy, 293/300 medium, and 298/300
  hard for seeds `1 + 101*episode`, 50 episodes × 6 pairs.
- Rotating motif shape with the same seed phase as the profile correlated the
  two schedules and reduced easy diversity to 257/300; that intermediate was
  retained as failing evidence and removed.
- Exact 100% uniqueness was rejected as an unrealistic diagnostic condition;
  the retained probe requires at least 90%, while the task regression requires
  at least 285/300 (95%) on its fixed production-shaped cohort.

### Limits

The semantic contract covers four explicit rivals, not all conceivable ARC
hypotheses.  Finite census and cyclic-window checks are evidence against those
rivals only.  Two range-sentinel slots are intentionally noncanonical profiles;
13/15 profile slots remain exact canonical size/palette anchors.
## Current reviewer considerations

Source SHA-256: `0aca61cb88fbe37ef9fcdb384bcb65460be8a4fad0081abade65b57ed392c57c`.

# Decisions: f84f23e456ac

All choices below apply to final generator version `3.4.0`, SHA-256
`0aca61cb88fbe37ef9fcdb384bcb65460be8a4fad0081abade65b57ed392c57c`.
The canonical Racket rule was left unchanged. The baseline contained no design
rationale beyond its source and short summary; where original intent was not
recoverable, it is marked unknown rather than inferred.

## D1 — Keep the authority; repair the sampler

**Choice.** Preserve canonical rule hash `54458840a785` and pin it as
`RULE_HASH`.

**Rationale.** Rule smoke and authority-sync were already green in the baseline,
and the five canonical examples were consistent with cropping the nonzero
bounding rectangle and tiling it in both dimensions. The defects were in the
input domain, controls, validation, and teaching support, not in the authority.

**Alternatives considered.** Changing the Racket rule was rejected because no
canonical mismatch or undefined lawful case was reproduced. A Python-only
semantic rewrite was also rejected; `rule_mirror` is explicitly a diagnostic
mirror, while Racket remains the source of truth.

**Probe/failure mode.** Final battery `rule_smoke`, `racket_lint`, and
`authority_sync` are green. A future rule edit must update both the canonical
row and `RULE_HASH`; the hash pin is intended to make silent drift fail.

## D2 — Replace pseudo-axes with six exact controls

**Choice.** Advertise only:

- `grid_h`: 6–20
- `grid_w`: 6–24
- `motif_h`: 2–5
- `motif_w`: 2–5
- `n_distinct_colors`: 1–2
- `density`: `sparse|dense`

Every explicit override is exact in every difficulty band. Unknown keys and
unknown bands raise `ValueError`.

**Rationale.** The baseline's texture/palette controls were overlapping or
unobservable, and difficulty-local restrictions rejected values that the public
axis declaration called lawful. A small exact surface is more useful for
training-data construction and easier to test than a large nominal one.

**Alternatives considered.** Keeping legacy aliases was rejected because it
would preserve ambiguity about which draw controlled the output. Declaring
band-specific incompatible endpoint combinations was rejected because the
underlying transformation has no such incompatibility.

**Probes.** Task tests exercise minimum, maximum, and interior joint overrides in
all three bands. The final `override` battery stage is green with no declared
incompatibilities.

**Limit.** Density is binary by design: sparse means nonzero count at most half
the motif area; dense means strictly more than half. It is not a continuous
occupancy control.

## D3 — Make the observed motif dimensions truthful

**Choice.** The sampled motif must occupy its requested bounding rectangle,
begin at `(0, 0)`, include at least one zero, and be primitive in rows and
columns. One of two opposite-corner pairs is nonzero, then support and colors are
sampled; accidental smaller periods are rejected.

**Rationale.** The baseline could request a motif height/width whose sampled
nonzero bounding box was smaller. That made override observations false and
could teach the model to infer period from a nominal rather than visible motif.
Primitive motifs remove equivalent smaller-period descriptions from the lawful
domain.

**Alternatives considered.** Forcing the entire border nonzero would guarantee
the box but create a strong border shortcut. A fixed L-shaped guard was
implemented and rejected after its easy-band cohort produced only 179/300
unique inputs.

**Probes.** `self_check` rejects shifted, out-of-box, no-zero, periodic, and
invalid-color impostors. The final task regression requires at least 285 unique
inputs in a fixed 300-draw cohort for every band.

**Limit.** Rejection sampling has a 128-attempt cap. No cap failure appeared in
the tested override and production cohorts, but it remains an explicit internal
error rather than silently relaxing the contract.

## D4 — Anchor ordinary draws without hiding declared range

**Choice.** Use a seed-rotated 15-slot canvas/color schedule. Thirteen slots are
one of the five canonical `(height, width, nonzero-color-count)` profiles; one
slot is `(6, 6, 1)` and one is `(20, 24, 2)`.

**Rationale.** Canonical-like profiles keep training examples near the observed
task distribution, while two ordinary range sentinels ensure the broad public
canvas axes are exercised without requiring overrides. Seed rotation prevents
all episodes from sharing the same profile phase.

**Alternatives considered.** Using only canonical anchors initially passed
profile gates but left the advertised canvas extrema unreachable in ordinary
generation; a red regression retained under
`checks/task-tests-red-axis-span/` caught it. Uniform canvas sampling was
rejected because it would make canonical support sparse and dilute the task's
observed scale.

**Probe.** A complete 15-slot cycle contains both range endpoints and at least 10
canonical profiles; the actual schedule contains 13.

**Limit.** The two sentinel slots are intentionally noncanonical. Consumers that
require only strict canonical profiles should use `strict_canonical_like` or an
appropriate profile filter rather than assuming every ordinary draw is strict.

## D5 — Separate motif schedule from profile phase

**Choice.** Use sample-index motif schedules independent of the seed-rotated
canvas/profile phase:

- easy: `2x3`, `3x2`, `2x4`
- medium: `2x4`, `3x3`, `4x2`
- hard: `3x5`, `4x3`, `5x2`

Density follows `sparse`, `dense`, `sparse` over the same three-example lesson.

**Rationale.** Each three-example lesson must show both horizontal and vertical
repetition and include at least one width other than three. Increasing motif
size with difficulty supplies a real, visible difficulty shift without changing
the rule.

**Rejected alternative.** Rotating motif phase with the same seed phase as the
profile correlated two independent features and reduced easy-band uniqueness to
257/300. That failed intermediate is retained at
`checks/task-tests-green-seed-rotation/result.json` despite the historical
directory name.

**Limit.** Only three motif shapes occur ordinarily in each band, though exact
overrides cover every 2–5 height/width combination. This is a deliberate lesson
schedule, not a claim of uniform joint support.

## D6 — Declare and kill plausible semantic rivals

**Choice.** Declare executable rivals for:

1. identity,
2. horizontal-only tiling,
3. vertical-only tiling, and
4. fixed motif width three.

Declare the fourth separately in `CANONICAL_SHORTCUTS`; it must first be shown
to fit all usable canonical pairs. `lesson_identifiable` reports a defect only
when a rival fits every demonstration and predicts a different query output.

**Rationale.** All five canonical motifs have width three, so correct labels
alone do not prevent a canonical-only shortcut. The intended rule must be
supported by the assembled demonstrations, not merely by individual examples
in the generator's total support.

**Alternatives considered.** Counting witness frequency was rejected because a
lesson can omit a frequent witness. The retained probe instead checks every
requested cyclic start under the actual consecutive-sample policy, and the
shared census tests production assembly plus every query rotation.

**Probes.** `checks/curriculum-probe-final3.json` shows the width-three shortcut
fits 5/5 canonical pairs and that no declared rival survives any of 100 cyclic
starts per band. `checks/lesson-census.json` reports zero ambiguity in 300
production lessons and 1,200 rotations.

**Limit.** Four rivals are finite hypotheses, not an exhaustive theory space.
An undeclared rule may still agree with all examples.

## D7 — Use a strict but attainable diversity regression

**Choice.** Require at least 285/300 unique inputs in a fixed production-shaped
cohort per band; retain a looser 90% threshold in the reusable workspace probe.

**Rationale.** The shared diversity smoke floor allowed a correct but tiny
finite family to pass at roughly 60% uniqueness. The 95% task regression is
strong enough to catch both the 179/300 fixed-support design and later
257/300–270/300 correlated designs while allowing occasional deterministic
collisions.

**Alternatives considered.** Requiring 300/300 was rejected because rare
collisions are not themselves a semantic or distribution defect. Relying only
on the shared 300-pair smoke stage was rejected because its acceptance threshold
was too low for this task.

**Final observation.** The fixed cohort yields 288/300 easy, 293/300 medium, and
298/300 hard. The separately seeded 100-draw workspace probe yields 99, 99, and
98 unique inputs.

## D8 — Retain a future-agent probe, but do not promote it to authority

**Choice.** Add `workspace/probe_curriculum.py` to report source hash, profile
support, uniqueness, canonical-shortcut fit, rival refutation, and every
requested cyclic lesson start.

**Rationale.** Future reviewers need a fast way to detect schedule regressions
without reconstructing the semantic analysis. The tool discovers rivals from
the generator's declarations rather than copying a stale name list.

**Alternatives considered.** Using the Python mirror as final correctness proof
was rejected. The probe's report explicitly directs reviewers to the Racket
battery and source-bound lesson census for authority-bound evidence.

**Limit.** The probe uses generated inputs and the Python mirror, so a matching
bug in generator and mirror could escape it. Authority checks remain separate.
