# Working notes: 2dacb90452ce

## Review 2026-10-04 — assignment `review-f4b6932b6f3357f6`

Prior return `review-db674f1f2060195b:v0001` (baseline generator SHA-256 `59e3240735feef52056bef7408c0a7345856e02a404fc81d77782c694572dd15`) was used only as a lead. I reproduced its `tiny_grid` exact-override/validator contradiction and independently measured missing `RULE_HASH`, area drift, degenerate ordinary textures, weak validation, and zero exact canonical-profile support.

The first repair (`3.0.0`, SHA-256 `5322c4994280ab11c5417971357d3a61cc3a0e8bd0a57fa0f08908451c1d4845`) narrowed generation to the four exact public profiles and passed the battery, tests, and census. Adversarial self-review then found a new profile-recognition shortcut: apply the correct rule only on the four public size/palette profiles and tile otherwise. That intermediate solve and evidence are retained under `checks/prior-solve-exact-profile/` and `checks/after/`.

Final version `3.1.0` keeps side lengths 2..5 but cycles palette cardinality by sample index: exact public count, one fewer, one more. Thus every three consecutive pairs contain one exact and two off-profile inputs; every two-demo window contains an off-profile counterexample. The declared `canonical_profile_only_else_grid_tile` shortcut fits all four canonical pairs but is refuted on 426/600 final semantic-census draws. Structural row-tiling, whole-grid tiling, and transpose-first rivals remain refuted per instance.

The selected Racket authority was not changed. Final generator SHA-256: `b972fe9cc491907d1193818efe9a68c28202c3cb355cf31fc1b0c7dd2779d4c0`; pinned rule hash: `511f58f5d471`.
## Current reviewer considerations

Source SHA-256: `b972fe9cc491907d1193818efe9a68c28202c3cb355cf31fc1b0c7dd2779d4c0`.

# Decisions for `2dacb90452ce`

## D1 — Keep geometry at canonical scale

**Choice.** Generate square inputs with side length 2..5.

**Rationale.** The canonical pairs use 2×2, 3×3, 4×4, and 5×5 inputs. The baseline's broad 2..15 texture field produced a median area far above the task and taught the simple upscale rule on visually unrelated data.

**Alternatives rejected.** Retaining 6..15 inputs preserved diversity but reproduced measured area drift. Restricting to one size would create a size shortcut and weaken output-shape coverage.

**Probe.** Final profile and diversity gates report all four shapes, 18/60 exact public profiles, and 100% unique inputs/outputs.

## D2 — Interleave exact and adjacent palette counts

**Choice.** For each selected side length, cycle visible-color cardinality by sample index: canonical count, one fewer, one more. Allowed sets are 2:{2,3,4}, 3:{3,4,5}, 4:{4,5,6}, and 5:{7,8,9}.

**Rationale.** Exact public profiles are necessary for canonical support, but an exact-only first repair admitted the rival “apply the right rule only on public profiles; tile otherwise.” Adjacent counts vary one factor without returning to the baseline's unrelated texture grammar.

**Rejected alternative.** Finalizing version 3.0.0 with 100% exact profiles. It passed the initial battery and census, but failed adversarial shortcut review. That intermediate evidence and solve were retained rather than relabeled as final.

**Probe.** The declared profile-gated shortcut fits all four canonical pairs and is refuted on 426/600 generated draws. The 300-lesson/900-rotation census measured zero surviving ambiguous queries.

## D3 — Preserve every selected color

**Choice.** Seed the cell multiset with every palette color, then fill remaining cells according to difficulty and shuffle deterministically.

**Rationale.** Palette cardinality is part of both canonical support and the shortcut witness. Selecting colors that can disappear would make observed profile counts nondeterministic and exact controls unverifiable.

**Failure mode controlled.** Accidental palette collapse. The validator checks observed counts; tests cover all sizes and bands.

## D4 — Use difficulty only for texture balance

**Choice.** Easy draws use a strong dominant color, medium draws mix dominance and random fill, and hard draws use a more balanced random fill. Geometry and the rule do not change by difficulty.

**Rationale.** This gives visual-density variation without teaching different semantics in different bands.

**Limitation.** Difficulty is not an advertised exact axis; it is a broad sampling policy.

## D5 — Advertise only `grid_size`

**Choice.** Keep one exact axis, `grid_size=2..5`; reject unknown keys. Palette count is a scheduled curriculum property, not a user override.

**Rationale.** The baseline had multiple interacting exact axes whose documented combination could return a 1×1 grid. A single observable control keeps the contract exact and the cross-product lawful.

**Alternative rejected.** Adding an exact `palette_count` axis would require structured incompatibility declarations for size/count combinations and would permit downstream lessons to select only exact profiles, defeating the schedule guarantee.

**Probe.** The final override matrix accepted 450/450 calls across three bands with zero findings.

## D6 — Separate lawful validation from strict public-profile validation

**Choice.** `self_check` accepts canonical and adjacent palette counts; `strict_canonical_like` accepts only the four exact public profiles. `MIN_STRICT_FRAC` is 0.25.

**Rationale.** Conflating the two validators would either reject the new counterexamples or falsely label them canonical. The final semantic census measured 174/600 strict draws (29.0%).

**Adjustment.** An initial 0.30 floor produced a transparent 29.0% warning on the pinned census. The floor was corrected to 0.25, below the measured rate but far above the shared near-zero default, then the full battery was rerun from fresh source-bound evidence.

## D7 — Reject per-instance structural aliases

**Choice.** Require horizontal and vertical variation, at least two varying rows/columns for size ≥3, and non-transpose symmetry. Reject row-tiling, whole-grid tiling, and transpose-first rivals on every generated input.

**Rationale.** Constant rows, symmetric grids, or minimal lines can make a wrong transformation answer-equivalent to per-cell upscale.

**Probe.** Each structural witness fired 600/600; each associated rival claim was oracle-checked 60/60. Named mutation fixtures are covered by task-local tests.

## D8 — Guarantee lesson-level refutation of the canonical shortcut

**Choice.** Exact profiles occur only at sample indices divisible by three; the other two residues are off-profile. `EXAMPLES_NEEDED=2`.

**Rationale.** Every two consecutive demonstrations therefore include at least one off-profile input, even before considering the query. Every three-pair rotation retains an off-profile demonstration.

**Probe.** Semantic smoke: 12/12 lessons identifiable. Expanded census: 300/300 lessons and 900/900 rotations, zero ambiguities, warnings, or scoring errors.

## D9 — Leave the Racket authority unchanged

**Choice.** Pin and mirror the existing `(upscale g 2)` rule; do not edit canonical source.

**Rationale.** All canonical outputs and 120/120 generated smoke cases matched it. The defects were entirely in generation and validation.

## D10 — Evidence and stopping rule

**Choice.** Stop after final-source battery, selected tests, expanded lesson census, final visible-only solve, two audits, and fresh-patch replay are all complete.

**Known limits.** The finite rival set cannot prove universal identifiability; scale remains bounded to 2..5; arbitrary downstream lesson reordering is not exhaustively enumerated. These are reported rather than inferred away.

## Proposed parametric extension 2026-10-23 — assignment `review-a5a2c76f7cf55423`

**Status: proposed isolated prototype; production generator and canonical authority unchanged.**
The nearby rule parameter is `scale_factor ∈ {2, 3}`, fixed once per episode.
`scale_factor=2` is the exact canonical source `(rule! (lambda (g) (upscale g 2)))`;
`scale_factor=3` changes only the repeat count. The invariant reasoning is still
cellwise color preservation followed by uniform expansion in both axes. Inputs
continue to come from the selected production generator, independently of the
hidden setting, and 5×5 inputs remain within a 15×15 output at factor 3.

The runnable prototype is `workspace/parametric/prototype.py`; its README records
the exact command. Retained evidence is
`checks/parametric/scale-factor-v1/report.json` (prototype SHA-256
`e49eb6bbfc68f55b4a7b9b56876b25a0878f7383a3dab1820e20d5fc3b83fb8b`). It
contains one factor-2 and one factor-3 episode, each with two demonstrations and
four distinct queries. All 12 chosen labels and all 12 counterfactual labels were
executed through Racket. Factor 2 reproduced 4/4 canonical labels. Every query's
demonstrations refuted the other factor; zero of eight queries were ambiguous.
Exact rule hashes are `511f58f5d47190acd7307da0e87d1e6d84d787e18b14ce8c3c14de0471730050`
for factor 2 and `2fea407be69fc4a77b9a3bd2cb1cf82d34ef69c54f82fdbee89ad3bb14815cdf`
for factor 3.

Focused task tests passed 45/45. A bounded adversarial probe covered 96 sampler
configurations (672 inputs), 16 Racket episodes, 96 chosen labels, 96
counterfactual labels, and 16 public projections with no finding. It attacked
sampler uniqueness/bounds, Racket shape and numeric parity, demonstration-only
rival rejection, public-field leakage, and content-ID independence from private
metadata and query answers.

Known limits: only factors 2 and 3 and their mutual rival are assessed; retained
evidence covers two principal episodes plus bounded probes rather than every seed
or lesson ordering. This proposal does not change approval or admit data to
training.
