# Current reviewer-native extension: canonical or observed odd-shape pose

Production version **4.1.0** is unchanged: generator SHA-256
`47cccb50e5a74b99c406706f9d1aeb15100451b53640e28eafc5216440574ef9`,
selected rule hash `18bdd6911037`. The default `pose=canonical` retains the exact
**1,716-byte** canonical Racket program, SHA-256
`27bae96c0fff8a536a7862ccffebfb040721843016c42dae1b2d06697f456aca`.
The alternative `pose=observed` selects the same singleton D4 shape class and
returns its observed tight crop in cyan. Production approval state is unchanged.

## Native contract and decisions

`workspace/parametric/` contains the adapter, implementation, promotion contract,
independent audit, exact canonical source and bound evidence. The expanded native
grammar accepts exact list grids with axes 1..30 and exact integer colors 0/2:
at least three red four-connected components, with exactly two shape classes
under rotations and reflections and multiplicities `(n-1,1)`. Shape, component
size and count are otherwise unrestricted; diagonal-only contact is lawful.

Seeds are exact integers 0..2**63-1. Counts are independent: 2..6 demonstrations
and 1..4 queries, ordinarily **3 demonstrations and 4 private queries**. Every
call constructs a matched six-demo/four-query bank before slicing, with separate
settings/demo/query random streams and fresh lists. Qualification explicitly
exercises all six demonstrations. Core A uses common F5 and singleton W5 with
equal area and 3x3 boxes; reflected common objects prevent rotation-only matching.
Core B uses the connected S13 witness to distinguish Racket's string ordering of
formatted coordinates from numeric tuple ordering, and includes diagonal-only
contact. Observed poses exclude a shared fixed D4 output transform. Large 30x30
demo/query scenes contain 405/320 red cells across the canvas.

The observed-pose Racket alternative has a real stored-tag dependency: A computes
and stores each object's D4 signature; B counts those stored signatures, selects
the unique class and renders its observed crop. Replacing only A's signature
expression by translation-only tagging splits the reflected common pair and
makes unchanged B choose a common object in core A. The protected witnesses use
seed 0 and seed 17 core A, with executed intermediate tags and changed final
outputs; this is not merely a recoloring or a claim based on code order.

## Current bounded evidence

All paths below are retained under the returned `WORK/` evidence root.

- `checks/004ca3500787/native-and-audit-tests-command.json` and matching XML:
  **131 focused tests passed** (38 native, 93 audit).
- `checks/004ca3500787/sampler-v1.json`: **96/96 requests passed**, covering
  145 distinct inputs, 64 distinct query inputs and 32 distinct 30x30 inputs.
  This sampler probe checks request contracts; it is not the label authority.
- `checks/004ca3500787/shape-teaching-audit-v1/private/audit.json` and
  `executions.jsonl`: **40 intended labels**, **124 hypothesis fits** from only
  the first two demonstrations, **120 refuted and 4 intended survivors**, zero
  extra survivors and zero query disagreements. The ledger records 304 requests,
  230 protected Racket evaluations and 74 cache hits. Task-source and protected
  runtime hashes were unchanged before/after the audit. Coverage is finite
  (seeds 0/17, both settings and the declared rivals), not universal uniqueness.
- `checks/004ca3500787/qualification/qualification.json` and `execution.json`:
  **qualified**, four jobs, six demos/four queries, **64 protected evaluations**.
  The source inventory is `workspace/parametric/evidence/manifest.json`.
- `checks/004ca3500787/causal-recipe.json`, `build_causal_recipe.py`, and
  `causal/{witness,replay}.json`: **two cases reviewer_replayed**, with four
  additional protected intermediate-tag evaluations, followed by protected
  full/counterfactual construction and replay.
- `checks/004ca3500787/preview/` plus `preview-export-command.json` and
  `preview-verify-command.json`: **four episodes and 16 one-query views verified**.
  The private v2 permutation preserves source-index/view-ID pairing.

The inherited production finding **`review-205ebfa3d89039c8:v0001` remains
unresolved**. Its arbitrary production query reassignment ambiguity is not
repaired or closed by this native extension. The new bank fixes demo/query roles;
public query shuffling changes only private query presentation order. Reviewer
readiness is recorded separately from **owner acceptance pending** and
**training_admitted=false**. Historical notes below are preserved byte-for-byte.

---

# Working notes: 004ca3500787, version 4.1.0

## Intended rule and domain

A zero-background input contains 3–5 separated red four-connected polyominoes.
All but one belong to the same free-shape class under rotations and reflections.
Return the singleton class in cyan, in the lexicographically least normalized
coordinate pose and a tight bounding box. Color roles are fixed. The selected
Racket rule remains `18bdd6911037`; all five canonical labelled pairs agree with
actual reference execution. No reference rule or approval status was changed.

Final generator SHA-256:
`47cccb50e5a74b99c406706f9d1aeb15100451b53640e28eafc5216440574ef9`.

## Current distribution and decision reversals

The 3/4/5/3 component-count cycle, finite shape bank, halo-safe placement slots,
size/palette support and six exact override axes are retained. Four ordered
demonstrations precede the generated query; `LESSON_SCHEDULE_PERIOD` is 4.

Prior choice: each count/dimension profile had a fixed target rank. New choice:
keyed rank variation, with a seed-keyed reflection teaching role assigned to one
of the two larger profiles and a separate nonlast role. The reflection role
excludes ranks that would let exact-pose, rotation-only or old-layout rivals
succeed; the nonlast role excludes the last rank. Other profiles vary more
freely. This removes the deterministic count/canvas target selector while
preserving named-rival witnesses in each consecutive four-example window.
Fully unconstrained rank sampling was rejected because rank 0 removes the
intended reflection witness in the measured cases.

Prior canonical-shortcut declaration: raw observed crop (only 4/5 canonical
matches). New declaration: last-component selection followed by canonical pose
(5/5). Raw crop remains a normal semantic competitor. The previous statement
that every four-example window has four different outputs was false and has
been corrected; repeated outputs are legitimate.

The first 4.1.0 iteration created its auxiliary role context after the main
instance context. The override checker observed the auxiliary context and lost
axis provenance. Role selection now happens before main-context construction;
the public observer regression verifies requested sample metadata and axis
records. The context fix preserves all 1,200 paired generated grids tested.

## Evidence and known limits

Final full battery: 12/12 green. Portable task tests: 11 tests plus 19 subtests.
The source-bound probe at `workspace/probe_distribution.py` measures seeds 0–24,
indices 0–15 and three bands: the frozen old-layout predictor falls from
1,200/1,200 baseline hits to 324/1,200; all 975 overlapping four-scene windows
refute all seven declared rivals and contain all seven witnesses. The exact
last-component and old-layout counterexamples are under `counterexamples/`,
with actual Racket receipt identities and regression coverage.

The 300-lesson Racket census has zero ordered production ambiguities, but
123/1,500 arbitrary holdout rotations are ambiguous. A seed-0 census covers all
four start residues in three bands: 12 lessons and 60 rotations, no ambiguity
at that seed. These are finite declared-rival checks, not universal induction.

Fixed slots, witness-induced nonuniform positional priors, finite shape support
and intentionally noncanonical default outlier poses remain limitations. Do
not shuffle arbitrary pairs into train/query roles under this result. Legal
exact overrides can change the default teaching profile; the default four-demo
lesson guarantee must not be generalized to arbitrary overridden mixtures.
Detailed source-bound counts, failures and commands are in this return's
`REVIEW.md`, `DECISIONS.md`, `RESULTS.json` and `checks/` evidence. Imported
associated notes remain historical evidence, not this current specification.
## Current reviewer considerations

Source SHA-256: `47cccb50e5a74b99c406706f9d1aeb15100451b53640e28eafc5216440574ef9`.

# Distribution decisions: 004ca3500787

This review uses the pinned 4.0.0 baseline, not an unintegrated prior return.
Historical metadata is context; all decisive claims were measured on source
hashes listed in REVIEW.md. The imported working notes were a placeholder, so
an original rationale is marked unknown when it was not explicit in source.
The final source is 4.1.0, SHA-256
`47cccb50e5a74b99c406706f9d1aeb15100451b53640e28eafc5216440574ef9`.

## Input and teaching choices

| Choice | Prior rationale / failure | Final decision, alternatives and evidence |
|---|---|---|
| Fixed 0/2/8 color roles | Required by the selected rule. | Preserve background, input object and output colors; color permutation would change the task. Canonical/Racket comparisons remain 5/5. |
| Separated four-connected polyominoes; 3–5 components | Domain and singleton-class invariant are explicit; arbitrary clutter is outside this selected task. | Keep finite shape bank and separation. Do not broaden shape size, connectivity or object count without new domain evidence. |
| Canvas size and canonical profiles | Small profiles retain canonical support; larger profiles exercise more objects. | Keep dimensions. Final exact canonical-size/palette support is 38/60 draws: 15/20 easy, 9/20 medium, 14/20 hard. Morphology alone cannot diagnose shortcut leakage. |
| 3/4/5/3 component cycle | Four profiles provide distinct teaching cases; count also exposed a fixed target rank. | Retain count cycle but decouple target rank. Changing canvas/count alone would conceal the symptom without repairing target selection. |
| Target position | Fixed per-profile ranks; original necessity unknown. Count and dimensions predicted 1,200/1,200 baseline scenes. | Use keyed rank variation. Final old predictor matches 324/1,200; all 12 count/dimension cells have multiple ranks. Larger profiles cover every rank over the measured seed set. |
| Reflection role | A fixed large profile supplied reflection/pose/count witnesses. Naive rank-0 placement removed all three witnesses in 75/75 diagnostic repaints. | Assign the reflection role to profile 1 or 2 using a seed-keyed draw; restrict that role's rank to preserve actual rival disagreements. Rejected unconditional uniform rank because it breaks ordered teaching guarantees. |
| Nonlast teaching role | Needed to refute the canonical-fitting last-component rival. | Profile 3 chooses a nonlast target. Exact seed-0/index-3 counterexample is retained with actual Racket output. This induces a disclosed nonuniform positional prior. |
| Safe placement slots | Explicitly provide fitting, nonoverlapping objects. | Retain them. Random vertical jitter was rejected because it can change reading-order rank and invalidate the witness argument; wider placement support is separate work. |
| Canonical output orientation | Fixed by selected authority. Default outlier poses require normalization. | Preserve canonicalization and default pose policy. The initial suspected canonical mismatch was disproved; no Racket edit is justified. Noncanonical default poses remain a distribution restriction. |
| Rival declarations | Raw crop was declared canonical-fitting despite one canonical mismatch. | Declare last-component canonicalization (5/5), retain raw crop as an ordinary competitor, and add the old count/dimension predictor as a generated-distribution rival (0/5 canonical fits). Tests/probe inspect actual declarations. |
| Output variety | Source prose incorrectly promised four distinct output masks per four examples. | Correct the prose. Final 975 windows contain two/three/four masks in 39/411/525 cases. Output uniqueness is not needed for the intended relation and would impose another sampling constraint. |
| Six exact axes | Callers must observe requested legal controls or receive structured incompatibility evidence. | Preserve axes and public provenance. Final override gate: 123,300 draws, 121,860 accepted and 1,440 explicit incompatible combinations, zero findings. |
| Auxiliary context ordering | Intermediate implementation registered its role context last, hiding main-axis draws from the public observer. | Construct the role context first. A red regression demonstrated the defect; final public observer metadata and six recorded axes are correct on 1,200 paired checks with unchanged grids. |
| Test portability | Legacy script import and fixed parent depth failed in the snapshot runtime. | Use public reviewer_support canonical helpers and task-relative importlib loading. Frozen root fixtures remain unchanged; final portable collection is 11 tests plus 19 subtests. |

## Lesson assembly and limits

The supported default policy is **four ordered demonstrations followed by the
production query**. The seed determines which broad profile teaches reflection;
four consecutive indices contain the complete profile cycle. In 25 seeds ×
16 indices × three bands, all seven rivals are refuted and all seven witnesses
present in each of 975 overlapping four-scene windows. Those windows are not
independent random samples. Forced override mixtures have separate domain and
compatibility support, not an automatic four-demo teaching guarantee.

The source-bound Racket census uses 100 hash-derived seeds per band and starts
0–99: 300 lessons, 1,500 pairs, 1,356 unique inputs, zero production ambiguity.
Arbitrary query reassignment produces 123 ambiguous rotations out of 1,500;
the exact retained example is `checks/rotation-limit.json`. A separate fixed
seed-0 census covers all starts 0–3 in every band: 12 lessons, 60 pairs, 24
unique inputs, zero production and zero rotation ambiguity at that seed. Its
narrower result does not negate the broader failures. No universal
identifiability, model mastery, or training admission is claimed.

All source identities, counts and retained failures are in REVIEW.md and
RESULTS.json. The reusable probe is task-local. General shared-tool suggestions
are separated in FEEDBACK_TO_CODEX.md; audit targets receive findings only.
