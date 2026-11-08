# Working notes: 552c2402dce3

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-07 review repair: mixed target orientations

The v3.0 sampler chose one missing-corner orientation per input, so a solver that
read the first target and broadcast that orientation across the grid matched all
1,024 sampled synthetic inputs and both canonical demonstrations, despite failing
the mixed-orientation canonical query. Version 3.1 assigns cyclic distinct
orientations to the 2–4 targets in every generated input and declares that
broadcast shortcut as a lesson competitor. The Racket authority is unchanged.
See `workspace/probe_mixed_orientation_gap.py` and the before/after reports under
`checks/` in the review return.

## 2026-10-07 review repair: rotation-robust curriculum

A 300-lesson census found production ambiguity 0/300 but 457/1,500 ambiguous
single-query rotations. The four-profile cycle supplied each tail or solid-square
witness only once in a five-pair lesson; rotating that pair into the query let
component-bounding-box or solid-growth rivals survive. Version 3.2 alternates
isolated canonical-like scenes with `full_curriculum` scenes that contain one
lawful tailed target, one three-cell line, and one complete 2x2 square. Every
five consecutive pairs contain at least two full-curriculum scenes, so removing
any one pair leaves all named shortcut witnesses while preserving a 50% source
of strict canonical-like scenes. The Racket authority remains unchanged.
## Current reviewer considerations

Source SHA-256: `7effe4b27cdcb80bca0d986d748dff9c1a728227654a1bd8e2cca5d70aea1768`.

# Decisions for `552c2402dce3`

## D1 — Preserve the local Racket authority

**Choice.** Keep canonical rule hash `014607f2a279` unchanged and repair only the
Python generator, its lesson contract, tests, and documentation.

**Why.** Racket application, authority sync, and all canonical examples agreed on the
same exact rule: fill the unique black cell in every original 2×2 window containing
exactly three cyan cells. The defects were in what the sampler taught, not in the
reference transformation.

**Rejected alternative.** Editing the authority to match the old homogeneous
sampler would have narrowed the actual task and contradicted the mixed canonical
query.

## D2 — Guarantee mixed orientations inside each grid

**Choice.** Assign target orientations as a cyclic sequence beginning from a
seed/sample-index-dependent offset. Every 2–4-target input therefore contains at
least two distinct missing corners.

**Evidence.** Before repair, `checks/mixed-orientation-gap-before.json` reports
orientation cardinality one for 1,024/1,024 grids and zero disagreements with the
broadcast rival. Final evidence in `checks/mixed-orientation-gap-after-v32.json`
reports 1,024/1,024 mixed grids, cardinality histogram `{2:463, 3:342, 4:219}`, and
1,024 rival disagreements.

**Rejected alternatives.** Random-with-replacement orientations could still emit
homogeneous grids and would need rejection sampling. A fixed four-orientation layout
would overconstrain two- and three-target examples. The cyclic assignment gives hard
coverage with no retries while still changing the starting orientation.

**Failure mode considered.** The cyclic pattern itself is learnable. It does not
change the correct output rule, and the local rule remains necessary because target
locations, counts, layouts, and profile fixtures vary. The semantic rivals and fresh
solve test the transformation, not prediction of the schedule.

## D3 — Alternate isolated and redundant full-curriculum scenes

**Choice.** Replace the four single-fixture profiles with two profiles:
`isolated_targets` and `full_curriculum`. A full scene contains the complete trio of
one tailed valid target, one unchanged three-cell line, and one unchanged solid 2×2.

**Why.** The first repair's four-profile cycle supplied some shortcut evidence only
once per five-pair lesson. The measured result was 0/300 production ambiguity but
457/1,500 ambiguous query rotations (`checks/lesson-census-v31.json`). Alternation
places at least two full scenes in every five consecutive pairs, so any one held-out
query leaves another full witness among four demonstrations.

**Rejected alternatives.** Increasing the lesson to more demonstrations would raise
training cost and change the declared contract. Randomly sprinkling fixtures could
still create witness-free lessons. Keeping separate fixture profiles while changing
the cycle would require more brittle combinatorial accounting than repeating the small
complete witness set.

**Trade-off.** Half of source profiles are intentionally noncanonical teaching
counterexamples. The strict-canonical hook still measured 213/600 hits (35.5%), above
the declared 10% floor, because isolated scenes remain and canonical dimensions are
retained.

## D4 — Make the grammar exact

**Choice.** `_analyze` accepts either no curriculum fixtures or exactly one of each
fixture in the trio. Partial or duplicate fixture combinations are rejected. All
foreground components retain a one-cell black moat, and targets remain exact local
3-cyan/1-black windows.

**Why.** The lesson guarantee depends on recognizing the complete witness set. An
acceptance-only checker would allow malformed partial scenes to claim the wrong
profile and silently weaken identifiability.

**Failure modes considered.** A fixture can accidentally create an extra qualifying
2×2 or connect to another component. Candidate placement plus the final analyzer
rejects those cases. The final grammar and self-check stages are green.

## D5 — Declare and test the actual shortcuts

**Choice.** Add `broadcast_first_orientation` to both semantic and lesson rivals, and
retain the existing component-size/bounding-box/solid-growth competitors. Add focused
pytest coverage for within-grid orientation mixing and every single-query rotation of
representative five-pair windows.

**Why.** The inherited battery was green before the repair because the missing rival
was not executable and ordered production checks did not require all query rotations.
A named rival turns the discovered counterexample into a permanent regression.

**Probe.** `workspace/probe_mixed_orientation_gap.py` derives its generated samples,
canonical split, and lawful mixed witness from the current source. Task tests use
`reviewer_support.find_root`, `canonical_path`, and `canonical_pairs` through the
runtime's portable task-test setup rather than relying on a fixed repository depth.

## D6 — Four demonstrations, arbitrary single query

**Choice.** Keep `EXAMPLES_NEEDED = 4`. The exported unit is five consecutive pairs:
four demonstrations and one query. The final contract supports any of the five pairs
being selected as the query.

**Evidence.** The required-rotation semantic gate passed its 12 source-bound smoke
lessons. The larger final census requested/materialized 300 lessons (100 per band),
scored 1,500 single-query rotations, found zero ambiguity/warnings/errors, and covered
1,496 unique inputs (`checks/lesson-census.json`).

**Limitation.** This establishes identifiability only against declared deterministic
rivals and tested cyclic starts. It is not a proof against undeclared hypotheses.
