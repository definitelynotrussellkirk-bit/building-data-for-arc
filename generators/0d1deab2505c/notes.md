# Working notes: 0d1deab2505c

## Review 2026-10-20: strict call boundary and arm-turn prototype

Assignment `review-f51be7ab3aae2421` used accepted return
`review-44f307c1cb52a1c8:v0001` as the current-design lead; its broad sampler,
parser, rivals, and canonical Racket authority were retained. The selected lawful
generation behavior and `RULE_HASH = a0364ffd781c` did not change.

The before defect lint found 30 strict-scalar warnings: non-literal integer seeds,
non-literal integer sample indices, and negative sample indices were accepted in
three difficulty contexts. `generate` now rejects bool/float/string/non-integer
seeds and sample indices before any draw, and rejects negative sample indices.
Focused red/green regressions live in `tests/test_review_084223.py`. Final
generator SHA-256 is
`3e4e00bfc44e8f1a4af12230238c9df1ec4cc074ed283dee290e4fbe564d7702`.

The requested parametric extension is an isolated **prototype**, not a production
rule change. `workspace/parametric/prototype.py` selects one episode-level
`arm_turn` value: canonical/default `half_turn`, or `preserve`. Object recognition,
tail direction, wall translation, tail transport, background, and color roles stay
fixed. Both exact Racket programs were executed; all three demonstrations and the
query distinguish the alternative, and the default program matches canonical
outputs. Retained evidence is `checks/parametric/arm-turn-final/`; program SHA-256
values are `3996639a398224699febb256f9248c09926784c7a5cb10ba1bc07a9dce84c55d`
and `4bdc1c8f210255d4cc023b4ba583cc8a4c7a91cf0929f5015065944e61f85a38`.

Final verification: 12/12 strict battery stages are green in
`checks/after-enumerated/`, including required query rotations and all declared
period-3 starts at schedule seed 0; 87/87 portable task tests pass in
`checks/task-tests/`. The source-bound 100-per-band census materialized 300
lessons / 1,200 allowed rotations with zero ambiguities, hook warnings, or scoring
errors; its exact hash-bound gzip is `checks/lesson-census-final.json.gz`. The
initial prescribed after run is retained at `checks/after/`: it was 11/12 only
because strict policy required explicit schedule enumeration.

Known limits remain: finite declared rivals do not prove unique induction; the
prototype covers two settings and one retained episode per setting; production
continues to use only `half_turn`; and the strict scalar repair changes only invalid
API calls, not lawful generated grids.

## Current implementation: v2.0.0

The previous sampler always emitted one creature on grids at least 10 cells
wide/high, held the input palette at seven colors, ignored tail_length, and
advertised invalid diagnostic textures as ordinary overrides. Its validator
only counted colors. This excluded canonical small/multiple-creature scenes
and did not test whether lessons distinguished the transformation.

The replacement generates one to four complete creatures on background 8.
Body arms use four distinct colors drawn from {0,2,3,5,6,7,9}, with independent
arm permutations. Palette size is the exact global color count, including
1,4,8. A cyclic allocation covers the entire selected palette without fixing
any color to an arm role. The Racket reference remains the label authority;
diagnostic_transform is a task-local Python diagnostic and rival scaffold.

### Ordinary support and lesson schedule

All difficulty bands retain the same semantic branches and canonical family
supports. EXAMPLES_NEEDED=3 and LESSON_SCHEDULE_PERIOD=3 expose the intended
three-demo lesson and exact schedule period. Phase sample_index % 3 is:

- 0: classic two-cell stems with two diagonal fork tips; size/count/orientation
  families (8x5,1,vertical), (8x8,2,horizontal), (9x13,3,vertical), and
  (18x17,4,horizontal). Shapes and colors are freshly constructed.
- 1: first-lane one-cell stem with fork, at least two creatures.
- 2: first-lane three-to-five-cell stem, straight or forked, at least two creatures.

In phases 1 and 2, other creatures independently vary their tails; the second
tail must differ from the first when no axes are pinned. This defeats both
reconstruction of the fixed canonical tail and copying the first observed tail
onto every creature. Any four consecutive ordinary draws contain at least two
examples refuting both shortcuts. Removing any one pair therefore leaves a
counterexample among three demonstrations. Every creature has independently
permuted arms and positive wall movement; every phase 1/2 scene has multiple
creatures. The five declared rivals also include moving without turning,
leaving tails behind, and moving only the first creature.

lesson_identifiable checks lawful inputs and reports a declared rival only if
it fits every demonstration but predicts a different query answer. A surviving
rival that agrees on this query is redundant, not evidence of ambiguity.
The diagnostic query prediction uses only the query input; the hook does not
read its stored answer. Invalid inputs return structural reasons before rival
evaluation. This is identifiability relative to the explicit rival family,
not a uniqueness claim over arbitrary programs. Explicit overrides are diagnostic controls:
they can deliberately remove a teaching branch; no lesson guarantee is made
for such constrained streams.

### Exact controls and compatibility

AXES exposes grid_h/grid_w 5..24, creature_count 1..4, tail_length 1..5,
tail_branch bool, tail_direction up/down/left/right, and palette_size 7..10.
Integer overrides reject bool, float, and string coercions. None means unpinned.
Unknown keys and unsupported values fail visibly.

observe_overrides reads only the returned grid. Direction, stem length, and
branching describe the first lane: topmost center for horizontal lanes,
leftmost center for vertical lanes. The stem is the consecutive axial blue
run beginning two cells from the center. A fork has two diagonal tips one
step beyond that stem. Explicit direction/length/branch pins apply the
specified attribute to every creature; unpinned secondary attributes vary.

Parallel three-cell-wide lanes with at least one empty lane gap protect
both source and destination geometry. For n creatures, the perpendicular
dimension must be at least 4*n-1 (and at least five overall). For a stem length
L, the axial dimension must be at least L+4 for a straight tail or L+5 for
a fork, including one spare movement cell. Palette size p also requires
p-3 <= 4*n. Feasible free attributes are selected before any keyed value is
recorded. An impossible pin tuple raises OverrideConflict(ValueError) with
incompatible_axes; it never clamps a pin or retries after recording a value.

no_creature, no_tail, and full_grid remain named negative fixtures outside
AXES. They fail structural self-check and cannot mix with ordinary axes.

### Structural domain and verification hooks

parse_creatures is independent of the lane recipe. It admits all canonical
inputs and general 8-connected winding tails, including tails that extend
past the body on another side. It requires a complete body, four distinct
legal arm colors, exactly one cardinal tail root, separate tail components,
ownership of every foreground cell, and disjoint translated creatures.
The full body-plus-tail bounding box determines displacement. Ragged grids,
boolean/non-integer cells, missing arms, ambiguous/shared roots, stray
foreground, and translated collisions are rejected.

self_check and strict_canonical_like report this complete structural domain.
Semantic witnesses are verified against named rivals by the official gate.
Focused tests and independent public-Racket probes live beside the generator;
source-bound battery/census receipts are in the review return.

Local development check: 432 ordinary draws across default/easy/medium/hard
passed structural validation; both tail-template rivals disagreed in all 288
noncanonical-phase draws. The Python diagnostic and both canonical-fitting
shortcuts matched the four stored canonical labeled pairs. These development
checks do not substitute for executed Racket evidence or source approval.

## Current owner acceptance

Accepted v2.0.0 exact controls, multi-creature/mixed-tail sampling and lesson witnesses. Reviewer reports 80 portable tests, 12/12 stages, 300 lessons and 1,200 rotations. Failed/interrupted reference observations remain retained. Canonical rule unchanged; selected target text synchronized. Semantic checks were not rerun. Generator approval binds these exact sources and does not admit model trajectories to training.
## Current reviewer considerations

Source SHA-256: `3e4e00bfc44e8f1a4af12230238c9df1ec4cc074ed283dee290e4fbe564d7702`.

# Decisions — review-f51be7ab3aae2421

## 1. Scope and inherited design

The selected task is `0d1deab2505c`, traced to supplied ARC training family `99caaf76`. I used accepted return `review-44f307c1cb52a1c8:v0001` as a design lead, then measured the pinned packet source independently. That source already had a broad structural parser, exact observable controls, three-phase teaching schedule, declared rivals, and an unchanged canonical authority. I therefore treated this as a bounded repair plus the requested isolated parametric authoring prototype, not a redesign.

The intended rule remains: detect each complete color-4 cross and its attached 8-connected blue tail; infer the cardinal tail direction; translate the full body-plus-tail bounding box in the opposite direction until it reaches a wall; carry the observed tail intact; and rotate the four body-arm colors by 180 degrees. Background remains color 8. The canonical rule hash stays `a0364ffd781c`.

**Rejected alternative:** replacing the accepted sampler or parser merely because this was a new assignment. The before battery showed one narrow API-boundary defect, not a distribution or semantic collapse. A broad rewrite would add risk without evidence.

## 2. Parametric extension: choose `arm_turn`

The requested nearby rule parameter is `arm_turn ∈ {half_turn, preserve}`. `half_turn` is the canonical/default setting; `preserve` performs the same object detection, tail-direction inference, opposite-wall translation, and tail transport, but leaves arm colors in their original orientation. The setting is selected once per episode from a deterministic SHA-256 seed and used for all three demonstrations and the query.

This parameter was chosen because it changes an executed transformation while preserving the family's object roles, spatial relation, and multi-step reasoning. Four distinct arm colors make the settings observably different without changing input grammar. Exact Racket programs were materialized for both values, and one complete retained episode per setting was executed in the protected Racket runtime. Every demonstration and query distinguishes the rival setting. The canonical/default program also matches the selected canonical outputs.

**Alternatives rejected:** palette reskins, grid size, object count, and sampling weights are not rule parameters. Changing tail direction would alter an input cue rather than the hidden episode rule. Changing the destination wall or tail ownership would be a larger semantic fork and would no longer be the smallest nearby family variation.

The prototype stays under `repo/generators/0d1deab2505c/workspace/parametric/`. It is **proposed**, not selected production behavior and not approval evidence. Production generation still uses only `half_turn` under the canonical authority.

## 3. Repair the strict call boundary only

The pinned before source SHA-256 was `24b57d0c9c06922e455ca7e97cef32a520e835c3a1cba6d036c20e809122764d`. Its battery was 11/12: `defect_lint` reported 30 strict-scalar warnings across three difficulty contexts. The source accepted booleans, floats, strings, or other non-literal integers as `seed`/`sample_index`, and accepted negative `sample_index` values.

I added a failing regression first for negative `sample_index`, observed the failure, then added the minimum boundary check. A focused lint rerun exposed the same root cause for `seed`; I added parameterized failing regressions for representative invalid seeds before extending the boundary validation. The final behavior is:

- `type(seed) is int` is required;
- `type(sample_index) is int` is required;
- `sample_index >= 0` is required;
- validation occurs before generator context creation or any draw.

**Alternatives rejected:** coercing with `int(...)` would collapse distinct caller mistakes and preserve boolean acceptance. Validating only downstream in shared context would broaden scope beyond the selected task and still leave schedule arithmetic exposed. Changing lawful seed/index mapping was unnecessary.

The final generator SHA-256 is `3e4e00bfc44e8f1a4af12230238c9df1ec4cc074ed283dee290e4fbe564d7702`. Lawful calls and all generated grids are unchanged by this repair.

## 4. Keep the Racket authority and version identity unchanged

No canonical data, Racket program, `RULE_HASH`, or generator version string was changed. Rule smoke, Racket lint, authority synchronization, and canonical execution parity all passed on the final source. The prototype's two Racket programs are separate workspace artifacts and do not replace the selected authority.

**Rejected alternative:** refreshing approval metadata or changing the canonical program to make the prototype appear selected. The packet explicitly separates proposed parametric authoring from production authority.

## 5. Treat the prescribed after failure as evidence, then satisfy the stricter schedule contract

The prescribed after command completed 11/12 on the final source. Its only failure was the semantic-stage warning `declared_period_not_enumerated`: all 12 sampled three-demo lessons and 48 query rotations were identifiable, but strict policy required explicit enumeration of the declared period-3 schedule. I retained that run at `checks/after/` rather than erasing it.

I then ran a new full battery with `--require-rotations-identifiable --enumerate-schedule-period --schedule-seed 0`. It finished 12/12 green. The fixed-seed schedule census materialized every start residue in easy, medium, and hard: 9 lessons, 36 pairs/query rotations, zero ambiguity, zero hook warnings, zero scoring errors. The normal semantic sample also measured 600/600 strict draws and accepted all 8 canonical inputs.

**Alternative rejected:** suppressing the warning or lowering strict policy. The complete period is only three, so finite enumeration is cheap and more informative. The shared-tool usability issue is documented as `F1` rather than patched outside the allowed task scope.

## 6. Keep both finite schedule evidence and broad sampler evidence

The production sampler census used 100 lessons per band with query rotation. It materialized 300 lessons, 1,200 pairs, 1,200 unique inputs, and 1,200 rotations with no ambiguity, hook warning, materialization error, or scoring error. Every declared rival was refuted in every lesson under this sample.

This is finite declared-rival evidence, not a proof of unique induction. The fixed-seed schedule enumeration checks every declared start residue at one seed; the random census checks broader sampling but does not exhaust all seeds. Both scopes are reported separately.

The raw census was 15,215,363 bytes. I gzip-compressed it deterministically only after recording raw size/SHA-256 and verifying a round trip. The retained archive is `checks/lesson-census-final.json.gz`; restoration metadata and both hashes are in `checks/lesson-census-final.compression.json` and `checks/lesson-census-final-compaction.json`.

## 7. Tests, solves, and self-review

Portable task tests passed 87/87 on the exact final generator hash, including the seven new review regressions/prototype checks. The post-repair visible-only solve used the same final generator bytes, made one revision, and matched all three demonstrations; earlier rule exposure is declared `yes` and no reference was consulted during that solve. The required pre-repair blind solve remains separate and records one 3/3-visible revision with exposure `no`.

Self-review found no new shortcut or distribution restriction from the repair: the added lines reject only invalid API calls before sampling, so every lawful seed/index follows the previous code path byte-for-byte. The isolated prototype does not participate in production generation, approval, or lesson assembly.

## 8. Audit targets remain untouched

`f898eb5adb5d` reproduced ignored exact overrides on its pinned source: requested dimensions/counts were not observed and the result matched the no-override control. `7eba3ddf13bd` reproduced 24 accepted invalid call scalars across three difficulty contexts. These are findings-only audits under `AUDIT.md`; neither target was modified.

## 9. Remaining limitations

Finite rival registries cannot establish identification against arbitrary programs. The period enumeration uses one fixed seed and three bands. The parametric prototype covers two settings and one retained episode per setting. No model-training or downstream accuracy experiment was run, and this return does not itself change training admission or generator approval.
