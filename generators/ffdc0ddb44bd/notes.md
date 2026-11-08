# Working notes: ffdc0ddb44bd

## Baseline diagnosis

The retained review index from `review-27f8c31f6124f652:v0001` was used only as
a lead. Its source hash matched the selected baseline
`21422069978f9d94efca28c00add5f0e1e6fddee9397f4e743141ca5362fe318`.
Fresh checks reproduced the important defects:

- no `RULE_HASH` pin;
- all three canonical 2-vs-1 inputs rejected by `self_check`;
- ordinary draws had five objects and six colours rather than canonical support;
- majority role was coupled to colour 2 and fixed anchors;
- declared texture/position axes were dead or included invalid fixtures.

The before battery was interrupted while later stages were pending; it is not a
completed aggregate pass. Its completed stages retained the lint, self-check,
defect-lint, and rule-smoke evidence under `checks/before/`.

## Repair decisions

1. Keep the canonical Racket rule unchanged and pin `RULE_HASH = "29652af15048"`.
2. Restrict the public axes to three exact, observable controls: `height`,
   `width`, and `majority_count`.
3. Restore the task's canonical manifold: one shape repeated 2..4 times plus
   exactly one normalized-distinct decoy.
4. Make semantic role independent of colour and placement with a four-state
   schedule crossing `(colour 2 is decoy, first object is decoy)`.
5. Use four canonical-profile defaults followed by four broad defaults, so every
   semantic role occurs both at canonical scale and off it.
6. Declare the two canonical shortcuts as semantic rivals and reject lessons
   where three demonstrations fail to refute a rival that differs on the query.
7. Keep `strict_canonical_like` equal to the lawful task manifold and retain a
   Python mirror only for testing; Racket remains label authority.

## Red/green history

The first focused regression run produced 53 failures and 8 passes. Tests first
pinned canonical acceptance, exact controls, role counterexamples, cyclic
four-pair/query-rotation identifiability, purity, determinism, and invalid-input
rejection. The initial repaired generator passed those tests but the complete
battery exposed an exact-profile miss in easy and medium. That failed run is
retained at `checks/after-failed-profile/`. A pinned-census regression test was
then added; it failed before the scheduling correction and passed afterward.

Final selected source:

- generator version: `3.0.1`
- generator SHA-256:
  `67ddcba432ed9f1a46c681ef377dcc1f1c90526cd23e9e10021cf6abd7eae838`
- task-test SHA-256:
  `85658f38528dd33513ca2015e72f895dc76cadfb7e5b4c7c03834b21163c788f`

## Final measurements

- focused task tests: 62 passed;
- native battery: 12/12 stages green, with query rotations required;
- profile floor: easy 7/20, medium 8/20, hard 9/20 exact canonical-profile hits;
- override matrix: 15,480/15,480 accepted draws, 172 cases, no findings;
- Racket smoke: 120/120 applications, 55 distinct outputs, 0 mirror mismatches;
- semantic census: 600/600 strict-manifold draws; both witnesses fired in every
  band; 12/12 smoke lessons and 48/48 smoke rotations identifiable;
- large lesson census: 300/300 lessons, 1,200/1,200 rotations, 1,200 unique
  inputs, zero materialization/scoring/hook errors and zero ambiguity against
  the six declared aliases of the two competitors;
- local finite-schedule probe: 96 four-pair windows, 384 rotations, zero
  failures, with all four profiles appearing 32 times per band.

## Limitations

The generator intentionally teaches a compact task grammar rather than every
possible arrangement of repeated polyominoes. Objects are at most 3×3 and there
is exactly one decoy. The lesson checks cover declared colour/position rivals
and exhaustive starts of the finite schedule used by the local probe; they are
not a proof of universal rule induction against undeclared hypotheses. Catalog
training approval remains a maintainer decision.
## Current reviewer considerations

Source SHA-256: `67ddcba432ed9f1a46c681ef377dcc1f1c90526cd23e9e10021cf6abd7eae838`.

# Decisions for `ffdc0ddb44bd`

## D1 — Treat the prior audit as a lead, not proof

**Input choice.** I used the unverified return named in
`evidence/review_index.json` because its source hash matched this assignment's
baseline. Its main claim was a colour-2 shortcut and canonical rejection.

**Probe.** Fresh baseline lint, self-check, and defect-lint runs independently
reproduced those defects.

**Alternative.** Trusting the prior return without remeasurement was rejected.

**Failure mode / limit.** The before battery was interrupted after only four
stages had evidence; pending stages remain unknown for the baseline.

## D2 — Leave the Racket rule unchanged

**Rationale.** The selected canonical rule solves all canonical pairs and its
behaviour matched an independent Python mirror on final generated inputs. The
problem was the sampler/validator/curriculum, not the transformation.

**Alternatives.** Rewriting the Racket rule or changing the canonical row would
increase authority risk without addressing the shortcut.

**Probe.** Final rule smoke applied the rule 120 times with no crash, mutation,
or mirror mismatch. Authority sync reports the selected canonical and target
sources identical at hash `29652af15048`; an archival `raw_code` variant is
textually divergent but execution-equivalent on canonical pairs.

**Failure mode / limit.** Python mirror parity is sampled. Racket remains the
label authority.

## D3 — Restore the canonical 2-vs-1 manifold

**Input choice.** Use one normalized shape 2..4 times and exactly one
normalized-distinct decoy. Permit three to five objects total.

**Original rationale.** Unknown; the baseline instead generated 3..4 majority
copies and at least one decoy, which excluded all three canonical inputs.

**Alternatives.** Keeping 3..4 copies, or adding multiple decoy shapes, would
remain farther from the task examples and complicate lesson inference without a
canonical need.

**Probe.** All three canonical inputs pass `self_check` and
`strict_canonical_like`; 60 final default instances and the native mutation
suite also pass/reject as expected.

**Failure mode / limit.** Exactly one decoy is a deliberate compact grammar;
other lawful repeated-shape scenes are outside this generator's declared domain.

## D4 — Decouple role from colour and position with a four-state schedule

**Input choice.** Cross two booleans: colour 2 is winner/decoy and first
row-major object is winner/decoy. Schedule profiles `0,1,2,3` by sample index.

**Rationale.** Pure random assignment can produce unlucky three-demo windows in
which a shortcut survives. A finite period makes every four-pair lesson and all
query rotations inspectable.

**Alternatives.** Fixed counterexample boards were rejected as low-diversity;
unconstrained random roles were rejected as hard to guarantee and reproduce.

**Probes.** The task tests exhaust cyclic starts and rotations; the workspace
probe checked 96 windows and 384 rotations. The Racket semantic gate observed
colour-2-decoy 278/600 times and first-object-decoy 312/600 times, with both
witnesses in every band.

**Failure mode / limit.** The schedule guarantees only the declared role
shortcuts. An undeclared hypothesis may still fit all demonstrations.

## D5 — Keep only exact, observable public axes

**Input choice.** Expose `height` 9..18, `width` 14..22, and
`majority_count` 2..4. Reject unknown, non-integer, Boolean, and out-of-range
controls.

**Rationale.** These values can be recovered from the grid and directly alter
task morphology. The baseline's position, density, palette, and texture
controls were fixed, dead, overlapping, or semantically misleading.

**Alternatives.** Keeping diagnostic-only axes would add interface surface with
no reliable observable contract.

**Probe.** Endpoint and cross-product task tests pass. The native override gate
executed 15,480 draws across 172 cases and three bands with no findings.

**Failure mode / limit.** Shape complexity is intentionally band-controlled,
not a public exact axis.

## D6 — Interleave canonical profiles with broader defaults

**Input choice.** Each eight-sample block begins with four canonical-scale
profiles (height 9/10, width 16, majority 2), one for each semantic role state,
then four broader scheduled profiles.

**Rationale.** The first repaired version varied dimensions broadly but failed
the native pinned profile floor in easy and medium. Canonical support must be
observable independently in each band and role state.

**Alternatives.** Relying on random rare hits failed reproducibly. Making every
sample canonical-sized would sacrifice useful diversity.

**Probe.** The failed run is retained at `checks/after-failed-profile/`. The
new test mirrors the native seed recipe. Final native hits are 7/20, 8/20, and
9/20 for easy, medium, and hard; the broad distribution still spans at least six
heights, six widths, and all three majority counts.

**Failure mode / limit.** Scheduled defaults create periodicity. Random shape,
colour, slot, and broad-axis draws still diversify concrete grids.

## D7 — Use three demonstrations and require every query rotation

**Input choice.** Preserve `EXAMPLES_NEEDED = 3`, materialize four consecutive
pairs, and allow each pair to be the query. `lesson_identifiable` checks the
three demos against both declared competitors.

**Rationale.** Three demonstrations are enough when the four-profile schedule is
used, and match the packet's intended lesson size.

**Alternatives.** More demos would cost training tokens; a fixed query position
would hide order-sensitive curriculum weaknesses.

**Probe.** Native smoke: 12/12 lessons and 48/48 rotations identifiable. Large
source-bound census: 300 lessons (100 per band), 1,200 rotations, and 1,200
unique inputs with zero ambiguity or execution errors.

**Failure mode / limit.** The census covers production sampling and declared
rivals; it does not enumerate all schedule starts or all possible rules. The
workspace probe adds finite cyclic-start coverage but uses the Python mirror.

## D8 — Add a cheap reusable authoring probe

**Input choice.** Add `workspace/probe_curriculum.py` rather than burying the
schedule logic only in tests.

**Rationale.** Future agents can inspect role-profile balance, all query
rotations, declared rival survival, witness counts, source hash, and native
profile-floor seeds in one JSON report before running the expensive Racket
battery/census.

**Alternative.** A task-specific notebook was rejected because it is less
portable and harder to include in automated review.

**Failure mode / limit.** The probe is explicitly non-authoritative and cannot
find undeclared rivals. It reports those limitations in its output.
