# Working notes: dc657616ec21

## Review target and retained lead

The selected baseline was generator SHA-256
`602fc12686d3f81f389ede98dd446bc7d22682f1be6b80b1374c5f9373f54992`,
version `3.0.0`, rule hash `51d1d5e43d4d`.  I used the accepted audit text
retained in `evidence/review_index.json` (`review-60c980982dcbb9a5:v0001`) as
a lead, not as a measurement of the selected source.  That audit identified the
canonical-fitting rival

`panel class = ceil(min(bounding-box height, bounding-box width) / 2)`

followed by pairwise class equality.  It reported that this rival survived many
three-example windows under the baseline generator and that no executable
semantic contract was declared.

## Baseline observations

* The authoritative onion-peel rule and the structural generator were already
  sound; the before battery had 11 green stages and one semantic-gate advisory.
* The task-local tests were not portable: they guessed a canonical-data path
  from `Path.parents[...]` and failed before collection in the staged runtime.
* The generator used many nonrectangular shapes, but it did not require a
  bounding-box counterexample in each ordinary input or lesson.  Consequently,
  shape diversity alone did not establish that the strongest canonical rival
  was taught away.

## Selected repair

Version `3.1.0` keeps the canonical Racket authority unchanged and makes the
teaching contract executable.

1. `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS` now expose the live
   `bbox_min_side` rival; `SEMANTIC_WITNESSES` exposes its disagreement predicate.
2. Every ordinary input schedules both a mismatch silhouette and an exact
   control.  When a true depth repeats, one repeated panel is bbox-misleading
   and the other is bbox-exact.  With two distinct panels, the generator uses
   adjacent true classes and assigns the lower class a misleading bbox, so the
   rival predicts equality while the intended rule predicts inequality.
3. `_reserve_bbox_witness_width` reserves enough panel width for the
   misleading silhouette without exceeding ARC's 30-column limit.
4. `_normal_lesson_errors` rejects an ordinary input whose bbox-derived
   equality matrix still matches the true depth-equality matrix.
5. `lesson_identifiable` checks labels and rejects any query on which a declared
   rival survives all demonstrations but disagrees with the intended answer.
6. Explicit lawful degenerates remain available only through their named
   texture overrides and are intentionally exempt from the ordinary witness
   requirement.
7. Task tests now use `reviewer_support.find_root` and `canonical_pairs` rather
   than a fixed source-tree path.

The final generator SHA-256 is
`5512b58f4b9ac1412a83152b0aeb56883831475e35def04edd41c67eaae6e941`.

## Test-first evidence

* Baseline portable task-test preflight failure: `checks/task-tests-before/`.
* Semantic tests before implementation: 10 passed, 22 failed in
  `checks/task-tests-red/`.
* Workspace-probe test before the tool existed: 32 passed, 2 failed in
  `checks/task-tests-probe-red/`.
* First staged portability attempt for the tool: 33 passed, 1 failed in
  `checks/task-tests-attempt-1/`; the final test locates either staged task layout.
* Final selected task tests: 34/34 passed in `checks/task-tests/`.

## Final measurements

* Full after battery: 12/12 green, no advisories, in `checks/after/`.
* Production lesson census: 300/300 materialized lessons (100 per difficulty
  band), 1,200 labeled pairs, 1,200 all-query holdout rotations, zero declared-
  rival ambiguities, zero hook/scoring/materialization errors, and 1,197 unique
  inputs.  See `checks/lesson-census.json`.
* The reusable workspace probe verified the live canonical shortcut on all
  three labeled canonical pairs, found a generated disagreement witness, and
  checked 128 consecutive windows / 512 holdout rotations with zero ambiguity
  at seed 1701.  See `checks/bbox-rival-probe.json`.
* Supported Racket `apply` confirmed the exact generated witness in
  `checks/shortcut-witness/`.

## Limits

These are finite checks against the single declared strongest rival.  They do
not prove induction uniqueness against every possible hypothesis or every seed.
The per-input witness requirement is deliberately stronger than merely placing
one witness somewhere in a lesson, but named degenerate overrides do not promise
ordinary teaching support.  No canonical row, Racket rule, or base authority
file changed.
## Current reviewer considerations

Source SHA-256: `5512b58f4b9ac1412a83152b0aeb56883831475e35def04edd41c67eaae6e941`.

# Decisions for dc657616ec21

## D1 — Preserve the authoritative rule

**Choice.** Keep canonical rule hash `51d1d5e43d4d` and all canonical/base data
unchanged.

**Rationale.** Canonical outputs, the Python mirror, rule smoke, and structural
checks agreed. The observed defect was lesson identifiability, not output
correctness.

**Alternatives considered.** Rewriting the Racket rule or changing canonical
examples. Both would have changed authority without evidence of an authority
bug, so they were rejected.

**Probe/limit.** After battery rule smoke and authority synchronization are
green. This establishes binding to the selected authority, not a proof that no
other rule can fit the finite canonical set.

## D2 — Treat bbox-min-side as the primary competitor

**Choice.** Declare the live rival
`ceil(min(bbox height, bbox width) / 2)` and pairwise equality.

**Rationale.** The retained prior return `review-60c980982dcbb9a5:v0001` named it
as a source-bound lead; it fits the canonical demonstrations and had survived
many baseline three-example windows. I rechecked canonical fit with current
code rather than copying the prior claim.

**Alternatives considered.** Area, rectangle width, color, and shape-name
shortcuts. Existing silhouette/color variation already makes those weaker; the
bbox rival remained both simple and demonstrably canonical-fitting.

**Failure mode/limit.** Declaring one rival can create tunnel vision. Final
claims therefore say “no ambiguity against declared rivals,” never universal
uniqueness.

## D3 — Require a disagreement in every ordinary input

**Choice.** Schedule one bbox-misleading silhouette and one bbox-exact control in
each ordinary generated input, then reject any input whose rival equality matrix
still matches the intended matrix.

**Rationale.** A witness somewhere in a long sample does not teach every lesson.
Per-input disagreement makes any three-demo window and any single-pair holdout
contain direct evidence against the rival.

**Alternatives considered.** (a) Randomly increase misleading-shape frequency;
(b) require only one witness per four-pair lesson; (c) rely on `lesson_identifiable`
resampling. (a) leaves rare ambiguous windows, (b) can fail after query rotation,
and (c) hides the distribution problem behind rejection cost. All were rejected.

**Failure mode/limit.** This stronger curriculum restriction narrows ordinary
morphology. Named degenerate textures remain explicit override-only edge cases so
lawful boundaries are still testable without weakening ordinary lessons.

## D4 — Use a mismatch/control role pair

**Choice.** With a repeated true depth, make one repeated panel misleading and
one exact. With two distinct panels, restrict ordinary depths to adjacent pairs
`(1,2)` or `(2,3)`, make the lower true class misleading, and keep the upper
class exact.

**Rationale.** Equality output depends on class relations, not numeric class
accuracy. A single misclassified panel is insufficient if all equality
relations happen to remain unchanged. The paired roles force a matrix-level
disagreement.

**Rejected alternative.** Permit the two-panel `(1,3)` pair. Available bbox
misclassification does not reliably collide with the other class, so the rival
can remain unequal and predict the same matrix.

**Failure mode/limit.** Two-panel ordinary inputs no longer cover every pair of
true depths. Three-to-six-panel draws still cover class 1–3 combinations, and
exact overrides/degenerates cover lawful edges.

## D5 — Reserve witness geometry rather than retry blindly

**Choice.** Transfer/add panel width until the mismatch panel can hold a
`(2d+1)×(2d+1)`-bbox thin silhouette, staying within 30 columns.

**Rationale.** A deterministic geometry guarantee is cheaper and more auditable
than unbounded rejection sampling.

**Alternatives considered.** Regenerate the whole layout until a witness appears
or shrink another depth class opportunistically. The former obscures accepted
indices and runtime; the latter changes semantics. Both were rejected.

**Failure mode/limit.** Width transfer can reduce blank margins in another panel,
but tests retain lawful placement and the diversity/grammar gates remain green.

## D6 — Make the semantic contract executable

**Choice.** Add `SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`, `WITNESS_RIVALS`,
`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `strict_canonical_like`, and
`lesson_identifiable` using pure deterministic functions.

**Rationale.** The before semantic gate had only an advisory because it could not
execute the known teaching obligation. Live declarations let the shared battery,
census, workspace probe, and future agents evaluate the same competitor instead
of copying a name list.

**Failure mode/limit.** Python mirrors are not authority. Racket `apply`, rule
smoke, authority sync, and the production census provide the source-bound
cross-checks.

## D7 — Keep three demonstrations and check all rotations

**Choice.** Retain `EXAMPLES_NEEDED = 3`. Test consecutive four-pair materialized
windows by holding out each pair once.

**Rationale.** Three is the established task floor and is sufficient after the
per-input repair. Raising it would mask rather than fix ambiguity and increase
training cost.

**Evidence.** The final census checked 300 production lessons and 1,200 query
rotations; the reusable bounded probe checked 128 starts / 512 rotations at seed
1701. Both found zero declared-rival ambiguities.

**Limit.** The production census samples the real sampler but does not enumerate
all seeds; the bounded workspace probe enumerates only its declared start range.

## D8 — Repair tests with portable helpers and retain red evidence

**Choice.** Use `reviewer_support.find_root` and `canonical_pairs`; add focused
canonical-fit, per-input witness, lesson-rotation, override, structural-impostor,
determinism, and workspace-tool tests.

**Rationale.** The original fixed path could not run in the staged task runtime.
The new tests were written before implementation and retained at each meaningful
failure.

**Failure mode/limit.** The stage duplicates tests in two layouts. The final
workspace-tool test has an explicit two-layout locator; shared-tool feedback F1
proposes removing that burden from future task authors.

## D9 — Build a reusable live-declaration probe

**Choice.** Add `workspace/bbox_rival_probe.py`.

**Rationale.** Future agents need a small source-bound tool that verifies
canonical fit, finds generated counterexamples, and checks complete lesson
windows/rotations without hard-coding competitor names.

**Limit.** It uses the selected Python mirror for bounded authoring diagnostics.
For authoritative output claims, use the retained Racket `apply` witness or the
shared lesson census.
