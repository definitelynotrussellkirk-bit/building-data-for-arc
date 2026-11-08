# Working notes: 96d4a788da47

## Current task account

**Intended rule.** Treat each non-zero monochromatic 4-connected component as an
object. Translate each object horizontally by its own minimum occupied column so
its bounding box touches column 0. Preserve its rows, color, cell count, and
internal shape. The selected Racket authority was not changed; it is pinned by
`RULE_HASH = "da14dfe7467e"`.

**Final source.** Generator version 2.0.0, SHA-256
`77f37922cf825e83c01c3d8e690a8a4496193a2e07bd3c95ca54dbf9e529b0a4`.

## Baseline finding

The imported version 1.1.1 was a generic blob template rather than a precise
contract for this task. Its battery had 4 blocking failures and 2 advisories:
missing rule pin/dead controls, an acceptance-only validator that rejected none
of 64 destructive mutations, strict scalar/texture defects, thousands of
ignored or mismatched override cases, no canonical-profile hit in easy or hard,
and no semantic witness/rival contract. Its placement loop could also silently
return fewer objects than requested.

Baseline evidence is retained under `checks/before/`; generator SHA-256 was
`88d876d6dd213bea05c32b64097e0ebd8cc1338af808e1b280b079dbb18cb4ba`.
No prior selected-task return was treated as truth. The passing task
`b90d4c3d5553` and shared documentation were consulted only as API/contract
examples; all claims here were remeasured on the pinned baseline.

## Selected repair

- Replace rejection-prone free placement with constructive disjoint row bands.
  Every requested scene contains exactly 2 or 3 distinct-color objects, every
  object starts right of column 0, and blank rows prevent output collisions.
- Reduce the public surface to three observable exact controls:
  `grid_h=7..14`, `grid_w=8..14`, and `n_blobs=2..3`. Unknown keys, booleans,
  non-integers, invalid difficulties, and out-of-range values fail loudly.
- Correlate a canonical-profile mode around `(7,9,2)`, `(8,10,3)`, and
  `(9,10,3)` with broad full-domain draws, rather than sampling dimensions
  independently inside an envelope.
- Require at least one nonrectangular object in every generated input. This
  directly refutes the canonical-fitting shortcut “move each filled bounding
  rectangle left,” while retaining rectangles elsewhere for variety.
- Add a structural validator, exact override observer, independent geometry
  oracle, executable semantic rival/witness, and source-bound fixed
  counterexample.

## Retained counterexample and tools

`counterexamples/bbox-fill-left.json` is a lawful 7x8 scene containing an
L-shaped object. The intended output preserves the missing corner; the rival
fills it. The file is bound to the final generator SHA and rule hash and is
covered by the portable task suite.

`workspace/reference_probe.py` independently extracts components, applies the
cell-preserving translation, evaluates the bounding-box rival, loads canonical
pairs through the public portable API, and observes exact axes. Usage is
summarized in `workspace/README.md`.

## Final evidence

- Full after battery: 12/12 green, 0 advisory, 0 failed.
- Portable selected task tests: 49/49 passed.
- Lesson census: 300/300 materialized lessons, 0 production ambiguities; all
  1,200 leave-one-pair-out query rotations had 0 ambiguities. Each lesson has
  three demonstrations and one query; the production sampler and required
  rotation policy were tested against the declared `bbox_fill_left` rival.
- Exposed post-repair solve: one revision, 3/3 visible examples; prior rule
  exposure declared yes, reference consultation declared no.

Evidence: `checks/after/`, `checks/task-tests-final/`,
`checks/lesson-census.summary.json`, `checks/lesson-census.json`, and `solve/`.

## Known limits and open findings

The generated grammar deliberately excludes touching/overlapping output paths,
multiple components of one color, objects wider than four columns or taller
than three rows, and scenes with an object already at column 0. Those exclusions
make examples clear and exact; they do not describe every mathematically lawful
input for the Racket rule.

The finite rival check establishes only that `bbox_fill_left` is refuted. It is
not a proof of unique induction against every possible hypothesis, nor is the
300-lesson census an exhaustive enumeration of all seeds. Training admission
remains a maintainer decision.
## Current reviewer considerations

Source SHA-256: `77f37922cf825e83c01c3d8e690a8a4496193a2e07bd3c95ca54dbf9e529b0a4`.

# Decisions for 96d4a788da47

Final generator SHA-256:
`77f37922cf825e83c01c3d8e690a8a4496193a2e07bd3c95ca54dbf9e529b0a4`.

## D1 — Preserve and pin the selected authority

**Prior choice.** The imported generator did not declare a `RULE_HASH`; the
original rationale was unknown.

**New choice.** Keep the selected Racket rule unchanged and pin
`RULE_HASH = "da14dfe7467e"`.

**Reason and probe.** Every labeled canonical pair matches an independent
component-translation oracle. `rule_smoke`, `racket_lint`, and
`authority_sync` are green. A rule change would add risk without repairing the
actual sampler defects.

**Failure mode/limit.** The Python oracle is test support, not the authority.
Final labels still come from the selected Racket implementation.

## D2 — Replace free blob placement with constructive row bands

**Prior choice.** A generic growth/placement loop retried random blobs and could
silently emit fewer objects than the advertised `n_blobs`.

**New choice.** Construct 2 or 3 connected polyominoes in non-overlapping row
bands separated by at least one blank row.

**Reason and probes.** This makes every legal Cartesian override combination
constructive, prevents output collisions after left translation, and makes the
object count exact. Boundary matrices run in all difficulty bands; the override
stage and 49 focused tests pass.

**Rejected alternative.** Keep rejection sampling and declare incompatible
combinations. It was less replayable, could underfill, and had no useful
incompatibility inherent to the chosen small domain.

**Limit.** Touching objects and shared row spans are intentionally out of the
training grammar even though some such inputs could be rule-lawful.

## D3 — Remove dead generic axes

**Prior choice.** The baseline advertised generic position, density, texture,
and other controls that were ignored or weakly observable.

**New choice.** Expose only `grid_h`, `grid_w`, and `n_blobs` with exact full
ranges and no incompatible products.

**Reason and probes.** These facts are directly observable from every grid and
useful for controlled variation. Unknown keys and invalid scalar types now
raise immediately. The strict override audit is green.

**Rejected alternative.** Preserve compatibility aliases. Silent acceptance of
misspellings or dead controls is worse than a loud migration error for training
replay.

## D4 — Correlate canonical profiles, then mix broad support

**Prior choice.** Independent generic draws produced weak exact canonical-profile
support; easy and hard had zero hits in the baseline 20-draw floor.

**New choice.** Draw a correlated anchor from `(7,9,2)`, `(8,10,3)`, or
`(9,10,3)` in a high-weight core mode, with a broad mode retaining every public
value.

**Reason and probes.** Exact paired profiles matter more than merely surrounding
the canonical envelope. `profile_floor` and `dist_gate` pass while 384 default
samples still cover at least 12 dimension pairs per band and both object counts.

**Rejected alternative.** Always use canonical dimensions. That would maximize
profile hits but create a fixed-shape shortcut and collapse useful support.

## D5 — Force a shape-preservation witness in every scene

**Prior choice.** Canonical examples use filled rectangles, so “fill each
bounding box after moving it left” fits every labeled canonical pair.

**New choice.** Every generated input includes at least one connected
nonrectangular object; other objects may remain rectangular.

**Reason and probes.** The task is about moving objects, not replacing them with
rectangles. The retained L-shape counterexample and executable
`bbox_fill_left` rival show the exact distinction. The semantic gate and 300
lesson census refute the rival in every production lesson and every tested
query rotation.

**Rejected alternative.** Add occasional irregular shapes IID. A rare witness
can disappear from a three-demo lesson, which is precisely the failure a small
model can exploit.

**Limit.** One finite rival does not prove universal identifiability.

## D6 — Keep the generated geometry small and explicit

**Choice.** Use connected polyominoes of 1–6 cells with bounding boxes no larger
than 3x4; all start at column 1 or later and colors are distinct.

**Reason.** Small objects make the transformation visually legible, fit every
minimum canvas, and keep exact construction simple. Distinct colors avoid an
unnecessary same-color component-association problem.

**Rejected alternative.** Broad arbitrary textures. The baseline showed that
nominal diversity without semantic control weakens validation and teaching.

**Limit.** The Racket rule itself is more general than this curriculum grammar.

## D7 — Make validation reject destructive mutations

**Prior choice.** The baseline `self_check` accepted all 64 destructive
mutations in the battery.

**New choice.** Validate dimensions, color types, component connectivity, object
count/size/bounds, nonzero left margin, and blank-row separation. Return
human-readable diagnostics rather than throwing on malformed grids.

**Reason and probes.** Blank, split-color, already-left, malformed, and
row-overlap examples now fail. The self-check and defect-lint stages are green.

**Limit.** `self_check` intentionally accepts all-rectangular canonical inputs;
the mandatory irregular witness is a sampler curriculum property, not a
universal validity condition.

## D8 — Add independent tests and reusable probes

**Choice.** Add `workspace/reference_probe.py`, 49 focused tests,
`workspace/README.md`, and a source-bound counterexample.

**Reason.** Reusing generator internals as the only oracle would let the same bug
agree with itself. The helper independently extracts components and computes
both intended and rival outputs. The portable `task_tests` stage confirms these
artifacts work outside the source layout.

**Evidence.** The first test-first run failed 35 of 48 original cases against the
baseline. The final suite is 49/49 green.

## D9 — Keep lesson assembly position-agnostic

**Choice.** Three demonstrations plus one query; require the declared rival to
be refuted even when any of the four pairs is held out.

**Reason.** Downstream assembly may rotate query position. The 300-lesson census
materialized 1,200 unique inputs and evaluated all 1,200 query rotations with
zero ambiguity.

**Limit.** This random census is source-bound but finite and tests only declared
rivals.

## D10 — Keep adversarial targets read-only

The assigned audit targets `576426a573af` and `f7660051ec70` were not modified.
Their current tests were run, and possible multiplicity shortcuts plus lawful
Racket-checked counterexamples were retained under `checks/audit/`.

## D11 — Add a native episode-fixed destination-edge family

**Choice.** Preserve the byte-exact canonical left-edge program (`da14dfe7467eb27b48e9064cdd2a94cb7af91dbed6045b9260887290c8d57131`) and add `right` plus per-object `nearest` settings, with nearest-edge ties resolved left.

**Reason.** Each variant retains object identity, color, rows, and internal shape while making the destination rule meaningfully different. Inputs are matched across settings, support 2–6 demonstrations and 1–4 queries independently, contain three row-separated irregular objects with both left-near and right-near cases, and include four novel queries up to substantive 30×30 boundary stress. Public views reveal only one input-only query at a time.

**Sequential dependency.** Step A measures each object's bounding-box left and right margins. The intermediate is the object-specific signed displacement chosen by the episode rule. Step B translates every original cell by that displacement. Replacing all measured displacements with constant `+1` changes the final protected-Racket output on the qualified nearest case.

**Evidence.** Focused tests 26/26; bounded self-audit 12/12 jobs with no surviving named rival; native qualification 6/6 jobs and 60 protected-Racket evaluations; changed-target tests 75/75; causal witness `checks/96d4a788da47/causal/witness.json`; inventory `workspace/parametric/evidence/manifest.json`.

**Limit and next action.** Evidence is finite and reviewer-reported; it does not prove universal identifiability or measured training gain. The owner must integrate the exact bytes, rerun native qualification, and perform fresh acceptance before any training admission.


## Current repeated-return reconciliation

Preserve exact left/right/per-object-nearest programs and canonical default. Add the incoming anchor-count-selected payload as a guarded setting: on the incoming one-to-three color-8 cells plus three non-anchor payload grammar, select the indexed row-ranked payload and slide it left; otherwise apply canonical all-left. Preserve both query-bank domains independently of setting; choose two visible lessons that also refute fixed-rank/size shortcuts. This explicit extension outside the incoming domain avoids discarding incumbent variety. Evidence: `evidence/reconcile-13/`. Private native qualification, fresh private acceptance and a fresh accepted episode passed. Live owner publication and training admission remain separate.
