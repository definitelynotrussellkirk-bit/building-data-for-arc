# Working notes: fc999420d3aa

Review `review-51747d880108f881` used the unverified historical audit
`review-15b1b10d11a63e6d:v0001` only as a lead. The baseline source hash was
`a408dea72c0fdc80b719e5a44d1d0ccac8f3638d2c37d9a49cb8bf13eb909383`;
the repaired generator hash is
`60ef94206b4b18d1cec6bfb88c2028d73747da828c67350eb62d661fc60e379a`.

The repair removes dead/redundant controls instead of pretending to honor them,
constructs every advertised exact-axis combination, guarantees distinct target
colors, pins the authority hash, and replaces silent one-template fallback with
backtracking placement or a loud error. Semantic hooks make the task's teaching
claim executable. The four-slot schedule deliberately keeps one canonical
anchor and three decisive controls; internal decoys may be omitted only on tiny
explicit override geometries because they are not an exposed axis.

Measured final evidence: 12/12 after-battery stages green, 26/26 selected task
tests, 18/60 exact canonical profile hits, and 300/300 Racket-labeled lessons
with 1,200/1,200 query rotations free of ambiguity against the three declared
rivals. These finite checks do not prove uniqueness against undeclared rules or
outside the documented one/two-target grammar. The Racket rule was not edited.
## Current reviewer considerations

Source SHA-256: `60ef94206b4b18d1cec6bfb88c2028d73747da828c67350eb62d661fc60e379a`.

# Decisions — fc999420d3aa

## D1. Treat the prior audit as a lead, not as current evidence

**Input choice.** I used `review-15b1b10d11a63e6d:v0001` to identify the
historical duplicate-color seed and suspected dead controls.

**Rationale.** Its source hash matched the selected baseline, but the assignment
requires fresh measurements. I reran the complete before battery and wrote a
new failing regression suite before implementation.

**Alternatives.** Accepting the old claims without reproduction was rejected.
Ignoring the lead would have repeated a useful deterministic census.

**Probe / result.** Baseline hash
`a408dea72c0fdc80b719e5a44d1d0ccac8f3638d2c37d9a49cb8bf13eb909383`;
before battery: 7 green, 2 advisory, 3 failed.

## D2. Replace the eight-axis fiction with three exact observable controls

**Choice.** Expose only `grid_h=5..18`, `grid_w=5..20`, and `n_motifs=1..2`.
Declare an empty incompatibility matrix because every Cartesian combination is
constructible. Reject misspelled, retired, out-of-range, boolean, float, and
string overrides.

**Rationale.** `palette_kind`, `n_decoys`, `palette_size`, `position_bias`,
`n_distinct_colors`, `density`, and `texture` either did nothing, aliased another
control, had a singleton domain, or generated examples outside the useful task
grammar. Silent compatibility would preserve misleading APIs rather than useful
variation.

**Alternatives.** I considered implementing all old controls. That would add
unnecessary policy surface and make small-grid Cartesian guarantees difficult;
several controls had no observable task-domain meaning. I also rejected merely
removing them from `AXES` while continuing to accept them silently.

**Probe / failure modes.** The final override stage exercised 319 cases over
28,710 draws in three bands with zero findings. The task tests enumerate all 32
boundary corners over four difficulty values. This does not test arbitrary
third-party callers that depended on retired keys; they now receive a deliberate
error.

## D3. Bound target count at two

**Choice.** `n_motifs` is exact over `1..2`.

**Rationale.** Two targets are enough to refute the “first target only” shortcut,
and every advertised combination remains feasible even on 5×5. The old upper
bound six was not honored and routinely triggered a silent one-target fallback.

**Alternatives.** Keeping `1..6` would require either incompatible size pairs or
larger minimum dimensions. Both would weaken the exact-control contract for no
semantic gain.

**Limit.** The canonical authority can act on more than two targets; this review
claims a bounded generator grammar, not the full authority domain.

## D4. Use backtracking with reserved absent-arm cells

**Choice.** Construct targets and optional decoys jointly. Filled cells cannot
overlap occupied or reserved cells; every absent arm remains zero. If an internal
decoy cannot fit on a tiny override grid, retry targets only. If exact targets
still cannot fit, raise instead of mutating the request.

**Rationale.** This makes the exact target count observable and prevents layout
interactions from changing the rule precondition. It also removes the prior
fixed-template fallback.

**Alternatives.** Greedy placement plus retries was simpler but could still fail
pathologically and conceal the requested count. Large fixed margins were
rejected because they make 5×5/two-target support impossible.

**Probe / failure modes.** All 28,710 override draws passed. The optional decoy is
not an exposed axis, so override lessons on minimum geometry may lack that
teaching witness; default decisive profiles fail loudly if any witness disappears.

## D5. Make target colors distinct and executable

**Choice.** Sample all target/decoy colors without replacement; enforce distinct
colors across firing centers in `self_check`.

**Rationale.** This matches the original prose promise and prevents two spatially
separate motifs from being visually conflated into one distributed object.

**Alternatives.** Relaxing the summary to permit repeated colors was possible,
but would retain the audited ambiguity and reduce object separability for model
training.

**Probe.** Historical easy seed/sample `(810027, 27)` now has two distinct target
colors. The dedicated regression prevents recurrence.

## D6. Use a four-slot curriculum: one anchor, three controls

**Choice.** Slot 0 is a canonical height/width/palette anchor. Slots 1–3 are
decisive profiles with two targets, a non-downward missing arm, and a two-arm
decoy. `EXAMPLES_NEEDED=3`.

**Rationale.** In a period-four sequence, every consecutive three examples still
contain at least two decisive controls; holding out any one of four labeled pairs
also leaves decisive evidence. Slot 3 makes the historical sample index 27 a
multi-target case while preserving canonical anchors at residue 0.

**Alternatives.** A period-three anchor/control/control schedule made index 27 an
anchor and lost the exact historical regression. Random witness occurrence was
rejected because complete lessons, not pooled frequencies, must carry evidence.

**Probe / limits.** Task tests cover starts 0..8 and all four query rotations;
the reusable probe expands this to 192 rotations. The production census checks
100 consecutive starts per band and 1,200 Racket-labeled rotations. Reordered or
independently assembled examples outside this policy require their own check.

## D7. Declare three concrete semantic rivals

**Choice.** `downward_only`, `first_target_only`, and
`complete_two_or_more`, with one witness mapped to each. The first two are also
canonical shortcuts because each fits all three canonical labels.

**Rationale.** They correspond directly to plausible overfitting: orientation,
single-object, and loose-precondition shortcuts. The witnesses are executable
and checked against actual output disagreement.

**Alternatives.** A prose-only semantic explanation was rejected. Adding a large
ad hoc rival library would increase maintenance without clear task-specific
plausibility.

**Probe / limit.** All three rivals are refuted in every one of 300 census
lessons and all 1,200 rotations. Undeclared rivals remain untested.

## D8. Keep canonical validation broader than generated construction

**Choice.** `self_check` accepts lawful canonical decoys and generated two-arm
decoys while requiring one or two firing targets, distinct target colors, valid
ARC cells, and supported dimensions. `strict_canonical_like` delegates to it.

**Rationale.** The third canonical input includes a non-firing color-6 shape
that should not be rejected merely because the new generator uses a simpler
decoy. Validation describes the teaching manifold, not one exact constructor.

**Alternative rejected.** Requiring every nonzero component to be a generated
plus/decoy template would reject canonical data and overfit the validator to the
implementation.

## D9. Leave the Racket authority unchanged

**Choice.** Pin `RULE_HASH=75975e426e4b`; add a Python mirror only for tests and
semantic diagnostics.

**Rationale.** Canonical labels, Racket smoke, and authority sync were already
correct. All observed defects were in distribution, contracts, and lesson
support.

**Probe.** Rule smoke, Racket lint, and authority sync are green. The selected
canonical authority changed by zero bytes.

## D10. Add durable tests and a small future-review tool

**Choice.** Add 26 task-local tests plus `workspace/review_probe.py`.

**Rationale.** The battery does not automatically discover selected task tests.
The probe gives future reviewers a fast check of the historical seed, exact-axis
corners, shortcut fit, and cyclic rotations; the Racket-backed census remains the
source of authoritative labels.

**Limit.** The quick probe uses the Python mirror, so it is a regression aid, not
a substitute for rule smoke or census.
