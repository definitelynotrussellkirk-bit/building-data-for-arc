# Current decisions — 84aeaf4792a8

## Authority and scope

Version `4.0.0`, generator SHA-256
`9e4da3766ae7f2cddf871ee9f2029c2b7d7655af119173f4be97ae78792e2ac6`.
The selected Racket rule `f2869336c461` is unchanged: order monochromatic
four-connected components by bounding-box minimum row/column; compare occupied
coordinates under translation and C4 rotations; emit diagonal 5, matches 8,
otherwise 0. Reflection and color-based ordering are not part of the rule.
All five labelled canonical pairs agree with that authority. An initial visual
suspect on the last pair was cleared by exact coordinates and Racket execution;
there is no canonical-label repair in this return (`checks/canonical-label/`).

The selected baseline was version 3.0.1, SHA-256
`73040ac4062a77bf02330ba37a9b9428f0e92f0a3c762c0147e87d594c2a8df9`.
Its associated-notes file was empty and no task review index was present;
historical rationale is unknown. No earlier return is used as current evidence.

## Repairs and reversals

- **R1 — make controls truthful.** Replace inert/singleton controls with five
  observable integer axes. Exact component/family/color requests either hold or
  fail with named conflicts. An unpinned component count grows for requested
  families/colors. Unknown names and coerced values are rejected. The original
  `(components=3, families=1, colors=1)` request emitted `(3,2,3)`; regression-red
  evidence is retained. The final shared override check accepts 55,170 of 56,970
  draws and explicitly rejects the 1,800 impossible combinations, with no findings.
- **R2 — broaden shapes and validate structure.** The four-shape bank becomes all
  19 rotation classes of connected 3–5-cell motifs fitting 3×3. Repeated colors on
  separated components are valid; blank, ragged, invalid-color, undersized motif,
  and touching-component grids are rejected. Guaranteed slot packing replaces
  silent failed placements. Canvas limits remain 8–18 by 12–22.
- **R3 — make the distinction teachable.** Declare six executable rivals and
  five actually canonical-fitting shortcuts. Even draws each refute area/bbox,
  reflection, translation-only, color-order, and forced-first-pair rules. Odd
  draws refute fixed-four outputs. Three demonstrations plus one query retain
  these witnesses under every single holdout in four consecutive default draws.
- **R4 — broaden relation proposals without weakening the witnesses.** The first
  repair overproduced tiny relation matrices (32 unique outputs in 144 lint
  draws). Phase 1 now proposes sizes 2,3,5 with weights 2,5,52; phase 3 uses six
  components. General family counts are weighted by Stirling numbers and each
  set partition is proposed once in its pool. This is a claim about proposals,
  not proven uniform final matrices after geometric ordering. Both intermediate
  failures and the later successful lint are retained under `checks/`.

## Current checks and replay pointers

`checks/after-final/result.json`: all 12 battery stages green on the hash above,
including required query-rotation identifiability, exact overrides, authority,
and canonical support. `checks/lesson-census.json`: 300/300 production lessons,
1,200/1,200 rotated query placements, 1,200 unique inputs, no ambiguity/scoring
or materialization errors. `checks/schedule-census.json`: all four cyclic starts
at seed 0 in three bands, 12 lessons/48 holdouts/17 unique inputs, no ambiguity.
These are finite checks against the declared rivals. Exact commands and final
focused-test/patch-replay receipts live in the return's `RESULTS.json`.

Task-local tests use an independent flood fill and rotation oracle plus portable
`reviewer_support` discovery. `counterexamples/reflection-and-bbox.json` is a
minimal legal chiral/coarse-statistic counterexample; selected Racket outputs
are retained at `checks/canonical-label/final-distinguishing-racket.json`.
`workspace/probe_distribution.py` records replayable default samples, actual
declarations, shape/partition support, and authoritative outputs for later agents.

## Limits and open findings

No blocking main-task finding remains. The sampler uses six placement slots,
reserves separator rows/columns, and does not cover every lawful arrangement.
Default four-component draws deliberately use only (2,1,1) and (2,2) partitions;
other four-component partitions are available through odd-index overrides.
Phase 1 favors five components; this improves relation diversity, not a balanced
component-count benchmark. Strict canonical likeness measures shape validity,
canvas/count/palette profiles, not equality to canonical relational patterns.
The unconstrained lesson guarantee does not extend to overrides that request
all-equal/all-distinct families or fixed component counts. Undeclared rivals,
larger motifs, and arbitrary spatial layouts are not certified. The nonblocking
diversity scanner still flags repeated matrices (reported 32% unique outputs
over 300 pairs); input uniqueness is 100%. Approval/training status is unchanged.
The two findings-only audits in this return concern other assigned tasks and
must remain tracked independently of this repair.
## Current reviewer considerations

Source SHA-256: `9e4da3766ae7f2cddf871ee9f2029c2b7d7655af119173f4be97ae78792e2ac6`.

# Decisions and limitations

## Assignment and authority

This return preserves assignment `review-44e73d0427e1d0cb`: main repair
`84aeaf4792a8`, blind solve `9c50790b939c`, audits `988bc6e81731` and
`2c41c09ae1d5`. Only the selected main task's source directory is patched.
The selected baseline, shared runtime, frozen tests, audit targets, catalog
approval, and training-admission metadata remain unchanged.

The final generator is version 4.0.0, SHA-256
`9e4da3766ae7f2cddf871ee9f2029c2b7d7655af119173f4be97ae78792e2ac6`.
The Racket rule pin is `f2869336c461`; its program-source SHA-256 is
`f2869336c461d64853b6f4c9664884ac2891c19088e7e3f0d8e1f23de406d092`.
The executed callable text SHA-256 is
`aeda4a710f394062484361427da309ac74c66b214a38e3256792f5710ca24dfe`.
No reference edit was justified: all five stored canonical pairs agree with
fresh authoritative execution and the independent coordinate oracle. A visual
misreading of the final canonical pair was investigated and disproved; the
comparison and both before/final source identities remain in
`checks/canonical-label/`. We did not rewrite a label to resolve a suspicion.

The main task had placeholder notes, an empty associated-notes file, and no
review index. Its historical design rationale is unknown. The actual baseline
code, not its stale three-component summary, was the subject of the before run.
Its version 3.0.1 hash was
`73040ac4062a77bf02330ba37a9b9428f0e92f0a3c762c0147e87d594c2a8df9`.

## R1: exact controls and visible failures

The original implementation declared controls it did not consume, silently
accepted unknown keys, and used narrower band-specific draw bounds than the
advertised domains. A requested three-component, one-family, one-color grid
actually contained three components, two families and three colors. These are
reproduced defects (`checks/regression-red.json` and `.log`), not inferred
from metadata alone.

The public controls are now only height 8–18, width 12–22, components 2–6,
rotation families 1–6, and distinct foreground colors 1–6. Values must be exact
Python integers: booleans, None, floats, and numeric strings fail. Unknown names
fail rather than pretending a typo was honored. These are observable properties
of materialized grids, measured by `observe_overrides`.

When component count is explicitly fixed, excess family or color requests are
incompatible and identify the conflicting axes. When it is unpinned, it grows
to accommodate a requested count. Clamping a requested count, ignoring it,
or making all multi-axis failures silently acceptable were rejected: each would
make the exact-control contract untestable. Limits are the same in all bands;
difficulty affects default proposals, not explicit legal ranges.

Removed palette/texture/density/position knobs were either inert, singleton,
or inadequately specified. This is an intentional API break, reflected in the
major version bump. Reintroducing them requires distinct, testable semantics.
Foreground color count is separate from component count; separated components
may share a color, and all colors 1–9 are available on broad draws.

Evidence: all 90 feasible (component,family,color) triples are tested on the
smallest canvas in all three bands (270 draws). The final shared contract check
performed 56,970 draws in 633 override cases across three bands: 55,170 accepted,
1,800 explicitly incompatible rejections, zero findings or warnings
(`checks/after-final/checks/84aeaf4792a8_after_override_results.json`).
A rejected impossible combination is not counted as a generation failure.

## R2: shape support, structural validation, and packing

The old four-shape bank is replaced by exhaustive enumeration of all 19
rotation classes of connected three-, four-, and five-cell shapes that fit in
3×3. Enumeration uses translations and the four rotations only. Both members
of a chiral pair are distinct classes. Shape geometry is cached; generated
grids, labels, palettes, and sampled arrangements are not.

This is a bounded expansion consistent with the small canonical motifs.
Unbounded polyomino sizes, reflection equivalence, and arbitrary large shapes
were rejected because they change the reviewed distribution or intended rule.
The independent test helper independently enumerates the same finite domain,
uses its own flood fill, and is compared with selected Racket outputs.

Six slots in two tiers and three columns guarantee placement of six motifs
on the minimum 8×12 canvas. A separator row and column in each slot prevents
both orthogonal and diagonal contact. This removes the old possibility of
silently dropping an unplaceable component. It is a deliberate spatial
restriction: not every validator-accepted arrangement can be emitted. Fully
random rejection placement was rejected because finite retries undermine
exact counts and complicate minimum-size feasibility.

The validator checks nonempty rectangular grids, exact integer colors 0–9,
canvas bounds, component count, three-to-five-cell motif sizes, 3×3 extents,
and separation between distinct monochromatic four-connected components.
It accepts repeated colors when components are separated. Color permutation
is often legal here; a mutation need not be rejected merely because it changed
a grid. Likewise deleting a component can leave a lawful smaller input.
Mutation rejection fractions are not advertised as perfect validator recall.

Strict canonical likeness additionally checks the canonical canvas envelope,
four components, four foreground colors, and palette {0,2,3,4,5}. It does not
assert that every accepted relation matrix occurs in the canonical examples.
The final profile-floor check has exact size/palette-profile hits 9/20 easy,
10/20 medium, and 9/20 hard; the semantic check separately reports 293/600
strict hits. These are different sampling populations and predicates.

## R3: explicit teaching witnesses and query policy

The strongest plausible canonical-fitting rival allows reflection as well as
rotation. The old bank cannot distinguish it: it never supplies both members
of a chiral pair. A second coarse rival compares area and unordered bounding-box
dimensions. Other declared competitors sort by color, force the first pair
to match, always emit four rows, or compare translated coordinates without
allowing rotation. Five fit all five labelled canonical pairs; translation-only
fits none and is honestly declared as a lesson competitor rather than a
canonical-fitting shortcut.

Default lessons use three ordered demonstrations and one query, assembled from
four consecutive accepted generator indices. The schedule has period four:

| Index modulo four | Main purpose | Default component/family policy |
| --- | --- | --- |
| 0 | Chiral nonmatch, quarter-turn match, alternative ordering | Four components; partition (2,1,1) |
| 1 | Broader size and relation proposals | Sizes 2,3,5; all feasible family counts |
| 2 | Repeat the distinguishing witnesses with two matched pairs | Four components; partition (2,2) |
| 3 | Broader large relation matrices | Six components; all feasible family counts |

Each even input individually refutes five shape/order rivals. Both odd inputs
refute fixed-four. Thus holding out any single pair leaves at least one
demonstration of every named distinction. Common tier row offsets on even draws
preserve the constructed ordering after rasterization. Color assignment is
checked so that sorting by color actually changes the observed matrix.
This is supported by independent tests and actual Racket-labelled lessons.

An ordered-only curriculum and a single special example were rejected because
removing that example as query would erase the witness. Merely increasing
single-grid counterexample frequency was also insufficient. The contract is
about complete lessons. Arbitrary explicit overrides are outside the teaching
guarantee: an all-equal-family or fixed-four request can deliberately erase
a needed distinction while remaining a valid exact input request.

The final required semantic smoke test checks 12 lessons. Wider validation is
`checks/lesson-census.json`: 100 lessons per band, three demonstrations plus
one query, 300 materialized lessons, 1,200 unique inputs, and all 1,200 possible
single query holdouts. Both production and required rotation verdicts are
`no_ambiguity_found`, with zero materialization/scoring errors, hook warnings,
or ambiguous rotations. Seeds use the report's SHA-256 recipe
`lesson-census:v1:TASK:BAND:INDEX`; requested starts are indices 0–99 in each
band and actual accepted indices are retained. The report's default residue
display modulus is six; it is not our declared schedule period.

A separate `checks/schedule-census.json` enumerates all four declared starts
at fixed seed 0 in easy, medium, and hard: 12 lessons, 48 holdouts, 17 unique
inputs because overlapping windows and bands reuse inputs. Both verdicts pass.
This fixed-seed exhaustive-start check is not mislabeled as 48 unique inputs
or an all-seed proof. No finite list of rivals proves universal induction.

The final visible-only solve uses the packet's separate three-demo/two-query
episode, not the one-query census format. Its actual hook status and solve
record are retained; the census's 1,200-holdout result is not extrapolated to
every possible two-query assembly.

## R4: revise relation weighting after an honest failed iteration

The first repaired version passed the semantic gates but failed lint:
the linter flagged a local variable named `objects`, and only 32 distinct
outputs appeared in 144 draws (reported 22%). Evidence for that source
(`505af9d…`) remains in `checks/after/` and
`checks/iterations/first-repair-generator.py`.

Some repetition is intrinsic to equality matrices and to repeated teaching
witnesses. Nevertheless the initial small-size schedule overproduced simple
all-equal or all-distinct outcomes. The final implementation proposes each
small-n set partition uniformly within its family count and weights family
counts by their Stirling counts. Phase 1 proposes sizes 2,3,5 with weights
2,5,52; phase 3 uses six components. This broadens the relation proposals while
retaining two canonical-profile teaching examples in each four-pair window.
A narrow regression checks all Stirling counts for sizes 2–6, uniqueness,
and valid restricted-growth encodings.

Final lint reports 61/144 distinct outputs (42%), with no warnings. The separate
50-episode diversity scan still flags repeated outputs (reported 32% unique
over 300 pairs) while input uniqueness is 100%. That scanner is nonblocking
in the supplied battery. We disclose the flag rather than treating a green
stage as a claim of uniformly distributed answers. Subsequent geometry-based
ordering can bias final matrix frequencies; only uniform partition proposals
are claimed.

The local-variable rename initially changed an import path as well. That typo
was reproduced and fixed before final validation; its source, failure log,
and receipt are retained under `checks/iterations/import-rename*`.
No failure was erased or repackaged as a natural solve error.

## Reusable tools and verification independence

`workspace/probe_distribution.py` reads the actual canonical-shortcut and
lesson-competitor declarations, verifies claimed canonical fits, uses public
Catalog.apply calls in batches of at most 64, and records exact inputs, outputs,
source identities, replay seed/index/overrides, class/partition/color support,
and each rival's first refutation. It refuses to overwrite prior evidence and
fails on invalid generation, authority mismatch, or a misdeclared shortcut.

Its retained run used seed 1729 and indices 0–127 in all three bands:
384 generated inputs, 320 unique inputs overall, 106 unique reference outputs,
and all 19 shape classes in each band. All 384 generated and five canonical
outputs matched the independent oracle and Racket. Each of the 11 namespaced
declarations (five shortcuts plus six competitors, with overlapping names)
has a refutation; these are six distinct rival rules. No six-family draw
appeared in this particular finite default sample; exact six-family support
is verified by the joint-control tests.

The final portable task-tests stage passed 181 tests in its isolated snapshot.
The first portable attempt failed because pytest was installed only in user-site,
which the test runtime intentionally suppresses. A separate local virtual
environment with copied installed dependency distributions resolved that setup
issue; source behavior was not changed for it. `checks/runtime-setup.json`
records the environment. The final handoff applied the exact patch in a fresh original extraction and
reran all 181 focused tests successfully with an independent environment.
RESULTS.json and checks/patch-replay/ retain the command, Git-root, patch,
source, dependency and test receipts. The full unrelated repository suite
was not rerun; selected-source gates, independent authority checks, portability,
and exact-patch replay address this change.

## Audit ownership, evidence, and stopping policy

The two other tasks are findings-only audits, with exact headings and scoped
reproducers in AUDIT.md. A988-1 is a new accepted-generated-input Racket crash;
A988-2 explicitly reproduces an earlier canonical-domain finding rather than
claiming new discovery. The second audit distinguishes a missing overwrite
teaching branch from incorrect labels on its sampled normal support. No audit
finding is treated as resolved by this main-task repair.

Lossless compression of the large intermediate green override case table is
documented in checks/COMPRESSED_EVIDENCE.json and checks/README.md, with original
path, size, SHA-256, and restoration instructions. All failures are retained.
The final full override result remains directly readable. The completed
source checks do not change training approval. Masked solve correctness stays
unknown until independent maintainer scoring.

## Review 2026-10-24: equivalence-policy native family

The approved production generator and canonical program remain unchanged. The new
native family is task-local under `workspace/parametric/` and introduces one
setting, `equivalence_policy`:

- `rotation` uses the selected canonical Racket program byte-for-byte and treats
  shapes as equal under the four rotations only.
- `dihedral` preserves the same object order and matrix rendering, but also treats
  reflected shapes as equal.

Inputs are setting-neutral. The curriculum supports 2–6 demonstrations and four
sequentially revealed queries; its first demonstrations expose chirality, rotation,
object order, and non-equivalence. Query sizes are 14×16, 18×20, 24×27, and 30×30.
The public projection reveals one query per turn and contains no setting, program,
answer, future-query, or total-query-count field.

The causal dependency is explicit. Stage A extracts foreground components in
bounding-box order and canonicalizes them under the chosen transform group. The
intermediate is the ordered vector of input-dependent shape-orbit class IDs. Stage
B renders the relation matrix from equality of those IDs (5 diagonal, 8 equal, 0
otherwise). On the retained qualified dihedral case the correct intermediate is
`[0, 0, 1, 1]`; replacing it with area/bounding-box keys changes the protected
Racket output, so Stage B cannot be selected correctly without Stage A.

Verification retained for this review:

- complete task suite: 218/218 tests;
- authoring audit: four episodes, 28 protected-Racket labels, zero findings;
- 16 sequential public exports, all structurally valid and leak-free;
- native qualification: two settings × seeds 0 and 17, three demonstrations and
  four queries per job, 40 protected-Racket evaluations;
- causal replay: two protected-Racket evaluations, status `reviewer_replayed`.

The finite rival audit and protected labels establish only the declared bounded
scope. Owner exact-source integration, fresh qualification/acceptance replay, and
any training decision remain separate. `training_admitted` is false.
