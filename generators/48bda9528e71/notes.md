# Current account: 48bda9528e71, version 2.1.0

Review return: `review-0766e77e77fc75b3`. Generator SHA-256:
`fa8f82d356825247d12033364a9c6de885922c2d3829e2de75399d211516cae6`.
The selected Racket rule is unchanged: `b9f9e9bda3f3`.

## Intended rule and admitted domain

Background is 8. Erase the single occupied shape and paint, in its unique
least-frequent foreground color, the in-bounds cell immediately beyond both
ends of every occupied row and column. The square canvas is 5..16 cells across;
the shape is 4-connected and contiguous in every active row and column, uses
two or three foreground colors, and occupies less than half the canvas. Every
rare-color cell has four occupied cardinal neighbors. Ordinary exterior
cardinal-neighbor outlining is answer-equivalent on this admitted domain.

## Reversed choice: convex-only sampling

Version 2.0.0's canonical profiles and general half-plane masks are lattice
convex. Consequently, filling their Euclidean convex hull before outlining
always gives the same answer. Retained audits
`review-19e0e8d6cd24f09c:v0001` and `review-0bdef3bb637751b2:v0001` identified this
coverage gap. The latter's prose said "orthogonal convex hull", but its retained
algorithm and separating witness concern the Euclidean hull; an orthogonal
closure cannot change an already orthogonally convex mask.

The new sampler retains all three canonical profiles and the old general
family, and adds rectangles with a rectangular corner removed. The two arms
and the two notch dimensions are at least two cells wide. The missing elbow
lies in the Euclidean hull but remains a required extent marker. It cannot be
clipped off the canvas, and its inside diagonal neighbor is a lawful rare-color
position. The minimum 5x5 witness and the rechecked historical 9x9 witness are
in `counterexamples/convexification_v2_1_0/`; both have actual Racket outputs.

## Lesson and override policy

`EXAMPLES_NEEDED=3` and `LESSON_SCHEDULE_PERIOD=4`. The default source-index
cycle is canonical, top-side notch, old general, bottom-side notch. Each group
of four consecutive draws contains two distinct separating inputs. Holding
out any one pair leaves a separating demonstration; no particular query
position is required. The two notch families have disjoint orientations, and
neither can duplicate a convex draw. This is a guarantee against the declared
`convexify_then_shell` rival, not all conceivable rules.

Exact `grid_size` remains 5..16; exact `scene_profile` remains canonical or
general. At noncanonical sizes, the canonical cycle slot becomes general.
Canonical-only overrides deliberately restrict the domain and do not refute
the rival. Nine impossible canonical-size combinations are explicitly
declared, not silently coerced. Unknown override keys and bool/float/string or
negative sample indices raise `ValueError`. Explicit size values must be
Python integers. Palettes, minority counts, the old convex family, and the
difficulty-dependent edge-placement bias are retained.

## Evidence and disposition

Fresh measurements of this generator are in the return's `checks/` directory:

- `convexification/`: 0/300 baseline versus 150/300 final default draws refute
  the rival in a Python-mirror census; seeds 0..99 per band, index `17*seed+3`.
  A separate supported Racket batch confirms 24/24 cases, including all eight
  symmetries of the minimum witness and the historical witness.
- `after-final/`: 11/12 battery stages pass. The only failure is exact-text
  synchronization of shared authorities; their execution parity passes.
- `task-tests-final/`: 30/30 task-local tests pass. Before the repair, these
  tests produced 29 failures and one pass after fixing the test environment.
- `lesson-census.json`: 300 actual three-demo/one-query lessons and 1,200 query
  rotations, 1,169 unique inputs, no ambiguity against declared rivals.
- `schedule-census.json`: all four starts at seed 0 in all three bands,
  12 lessons and 48 rotations, 20 unique inputs, no declared-rival ambiguity.

Both retained convexification findings are addressed by this proposed repair
and these fresh measurements. Their original text, source identities, and
evidence remain intact. This is reviewer-reported resolution pending intake,
not a catalog approval or training-admission change. A separate optional
shared-file formatting patch and a guarded builder are included in the return;
no authority source in the active review tree was changed.

## Remaining limits

The new nonconvex family covers single rectangular notches, not every lawful
orthogonally convex shape. Arbitrary two-demo query rotations are not promised.
The finite censuses are not universal identifiability or model-performance
measurements. The post-repair solve discloses earlier rule exposure and has
visible-only feedback; hidden query correctness remains unknown.

Imported historical notes retain their original evidence and timestamps in
`evidence/associated_notes.jsonl`; they are leads, not final-source test results.

## Current maintainer source selection

Only selected `racket_target.target_code` changes are retained; original archival `raw_code`, the canonical ledger and selected canonical rule are preserved. For 0162460030af, the return rewrote the archival field too; that part was reversed. Owner static field/byte checks are recorded in `evidence/current-authority-sync.json`. Returned fresh-copy test/battery results remain reviewer-reported, and the corrected owner source has not had a new battery.

## Current audit resolution

Convexification rival repaired: v2.1 guarantees two concave witnesses in every four-slot production cycle, preserving one under every single query holdout. Retained actual-Racket counterexamples and reported rotated/fixed-period evidence cover this named rival. The prior orthogonal-hull wording is corrected in current notes: the implemented shortcut was Euclidean hull. Full prior findings and retained evidence pointers: `evidence/current-audit-assessment.json`.
## Current reviewer considerations

Source SHA-256: `fa8f82d356825247d12033364a9c6de885922c2d3829e2de75399d211516cae6`.

# Decisions for review-0766e77e77fc75b3

The assignment is unchanged: repair `48bda9528e71`, blind solve `7fd453cd0339`,
and findings-only audits of `7946249c9684` and `b2f8fcc010d5`. All claims below
refer to retained evidence, with before, intermediate, and final sources kept
separate. No catalog approval or training admission was changed.

## D1 / R1: Repair the sampler; keep the intended Racket rule

The current rule's row/column extent output is correct for the documented
domain and all checked canonical cases. The defect is that the old sampler
cannot teach a distinction already admitted by its validator. Its half-plane
construction and canonical profiles are lattice convex; the accepted concave
witness is not. The two retained audits of this same baseline were useful
leads, not new measurements. Fresh baseline sampling and Racket checks
reproduced their substantive finding.

I rejected shrinking the validator's domain to convex shapes. That would
formalize the shortcut instead of teaching preservation of admitted concavity.
I also rejected changing the Racket rule to a Euclidean outline, which would
contradict the accepted witness. The canonical Racket program, selected rule
hash `b9f9e9bda3f3`, and archived programs remain unchanged in the task delta.
The optional formatting proposal is a separate shared-file decision, D7.

## D2: Construct a provable concave witness family

The new family starts with a rectangle and removes one corner rectangle. Each
arm width and each removed dimension is at least two. The resulting shape is
4-connected and orthogonally convex, has enclosed cells available for the rare
color, and has an absent integer midpoint in its Euclidean hull. At least that
missing elbow distinguishes the rival; its location is internal to the
bounding rectangle, so canvas clipping cannot hide the distinction.

Feasible dimensions are enumerated within the existing occupancy limit, and
the selected shape receives existing palette/rare-cell and offset sampling.
Even a 5x5 canvas supports a 4x4 shape minus a 2x2 corner, with 12 foreground
cells and 13 background cells. Increasing difficulty permits larger shape
spans (5, 7, and 9) while retaining the existing edge-contact biases (0.25,
0.55, and 0.80). D4 orientation and translations remove dependence on one
absolute corner. Fixed background 8 remains a domain property; other palette
roles remain randomly assigned rather than numeric-rank-coded.

Rejected alternatives: occasional unconstrained random concave masks provide
no reliable lesson-level guarantee; one-cell chamfers can remain lattice
convex and fail to separate the actual rival; an exhaustive sampler of all
orthogonally convex masks is unnecessary for this demonstrated defect and
would add substantial complexity. The chosen family is intentionally limited
to single rectangular notches. Its purpose is to remove the proved convexity
restriction while retaining the old support, not claim complete domain coverage.

## D3: Three demonstrations with a four-phase schedule

The cycle is `canonical`, `notch_top`, `general`, `notch_bottom` and the declared
period is four. There are two separating pairs in every four consecutive
source indices. Their allowed D4 transforms place their missing corners on
disjoint top/bottom sides, so they cannot duplicate each other. They are
nonconvex while the other two phases are convex. Consequently each default
four-pair window contains distinct pairs and every single-pair holdout leaves
a separating demonstration. At a noncanonical exact size the canonical slot
becomes general; even if convex draws duplicate and assembly advances, it
cannot lose the two distinct notched witnesses.

One witness in a four-pair lesson is enough for ordered production only when
that witness is guaranteed to be a demonstration; it is inadequate for
arbitrary query holdout. This is why there are two witness phases. Merely
increasing the number of independent random demonstrations would reduce but
not eliminate the chance of an unresolved rival. Two demonstrations can
suffice for some ordered cases, but arbitrary two-demo rotations are not part
of the guarantee. `EXAMPLES_NEEDED=3` matches the actual export policy tested.

Evidence: final semantic smoke has 12 materialized lessons and 48 required
rotations; the larger production census has 300 lessons and 1,200 rotations;
the explicit schedule census has all four starts at seed 0 in all three
bands, 12 lessons and 48 rotations. All report no ambiguity for the declared
rival. Unique inputs are 1,169 in the larger census and 20 in the overlapping
fixed-seed windows. The larger census alone is not schedule exhaustion; the
separate enumeration addresses its warning. No universal or all-seed
identifiability claim follows from either finite measurement.

## D4: Retain canonical and exact-control support

The original three canonical profiles are preserved in full up to D4 and
interchangeable foreground-color renaming. The canonical phase is one quarter
of default source indices; the general phase preserves the old convex family.
Default measurements find 25/100 canonical-profile draws per band, compared
with 44/100 in the pinned baseline under the same seed/index recipe. That
change is deliberate: half the cycle now supplies separating evidence while
one quarter retains the canonical teaching anchor. The final semantic gate
measures 137/600 strict-profile hits and the profile-floor stage passes.

Exact axes remain `grid_size=5..16` and `scene_profile=canonical|general`.
Canonical examples exist only at sizes 5, 7, and 16, so the nine other
canonical-size combinations are explicitly declared incompatible. Exact
general uses both convex and notched shapes and never silently switches to a
canonical profile. An exact canonical request intentionally excludes notches;
the rival is then equivalent on the requested population. I rejected honoring
a size request by silently changing the size or teaching profile.

The override checker reports 3,510 attempted draws, 2,700 accepted exact
requests, and 810 declared-incompatibility rejections across 39 cases and
three bands. There are no findings or unknown-key acceptances in the final
strict policy. These numbers are request-validation results, not 3,510
distinct generated inputs or universal joint-axis coverage.

## D5 / R2: Reject malformed controls at the public boundary

The baseline defect linter reproduced coercion of `sample_index=True`,
`False`, `1.0`, `"1"`, and `-1`. The repaired entry point requires a nonnegative
Python integer, excluding bool, before constructing the random context. Exact
size likewise rejects non-integer values, and unknown override keys raise
`ValueError`. This makes unsupported requests explicit and preserves the
existing semantics of valid calls. The final defect and override stages pass.

## D6: Executable rivals and independent focused tests

`convexify_then_shell` is registered in all three supported rival namespaces;
the semantic witness declares a matching geometry predicate. The strict
canonical hook recognizes complete profiles rather than a loose shape proxy.
The reusable distribution probe iterates the actual declarations, so a future
name change cannot silently leave a hard-coded rival list untested. Its
actual Racket outputs remain separate from Python-mirror distribution counts.

The new task tests check literal expected outputs, independent missing integer
midpoints, all schedule starts, query holdouts, canonical labels through the
portable `reviewer_support` helpers, exact controls, and minimum-canvas edge
placement. They do not derive their expected concavity from the implementation's
hull function. The root frozen fixture was not edited.

The first preflight discovered that the portable checker correctly isolates
user-site packages and could not import pytest. That infrastructure failure
is retained in `checks/regressions-before/`. A local venv with pytest installed
directly and permitted runtime NumPy/Pillow then produced a real red result:
29 failed, one passed on the original generator. Both the intermediate and
final repaired versions passed 30 tests. The intermediate generator differs
from the final only in a corrected docstring; its evidence remains labelled
intermediate, not substituted for final-source results.

## D7 / F1: Separate the shared authority formatting proposal

Four selected authority records contain two exact strings but one normalized
program; execution parity already passes. The task-only after battery therefore
has 11 green stages and a failing `authority_sync` stage. The optional patch
copies the existing formatted canonical text into two selected `target_code`
fields. It changes no canonical ledger record, archival `raw_code`, example,
catalog mapping, or normalized rule. The hash-guarded builder verifies these
limits and refuses unexpected source bytes.

This proposal is kept in `checks/authority-proposal/generated/authority-sync.patch`,
outside the allowed task delta, for an explicit maintainer selection. Its
retained small replay tests the unchanged synchronization checker and a
deliberate wrong-hash refusal. A separate full relocated battery with this
proposal passes all 12 stages, including Racket execution parity. The active
review tree keeps its original shared authority bytes and its honest 11/12
task-only result.

## D8: Keep solves and audits honest about scope

The blind solve was finished before repair or reference inspection. The later
solve was prepared from final generator bytes and disclosed earlier rule
exposure; no generator, reference program, or private labels were consulted
during its solve phase. Each contains one genuine authored revision, 3/3
visible successes, and two executed query predictions. Hidden correctness is
withheld. Notes are authored work summaries, not captured token-level traces.
No failed solve was fabricated to create a positive/negative pair.

The two random audits are findings-only and leave their source unchanged.
`7946249c9684` has a new column/color-extrema shortcut on all default
constructors, separated by an exact-override witness. `b2f8fcc010d5` has a
canonical-compatible corner swap that survives the demonstrations of an
actual default lesson and disagrees on its query. The retained evidence
distinguishes actual Racket labels, broader Python screening, and source
arguments. Audits are not repairs or approval decisions.

The first provisional package attempt rejected a direct edit to the selected
task's frozen evidence index. I restored its exact original bytes and retained
the proposed dispositions separately in `checks/resolution-proposal/`.
Maintainer intake can resolve the two prior findings using the repair evidence;
the reviewer does not overwrite the evidence index or its approval history.
The rejected package receipt is preserved in `checks/return-validation/`.

## D9: Preserve broader failures and perform an independent handoff replay

The optional full repository pytest run completed with 597 passed, four
failed, three skipped (Torch unavailable), and 18 subtests passed. None of the
four failures names this repair task. Focused original-copy reproduction and
diagnosis are retained under `checks/repository-tests/`; no baseline test is
rewritten to manufacture a pass. This global suite is reported separately
from the explicitly collected task-local tests.

For the final handoff, the exact builder-produced task patch was applied to
a new extraction of the original upload, inside a verified independent Git
root. All eight changed-file hashes match, the relocated focused tests pass
30/30, and the generator bytes match the final solve and final check hashes. This checks
the delivered delta and portable test layout rather than merely repeating a
test in the authoring tree. Full receipts are under `checks/return-validation/`.

## D10 / F3–F4: Build bounded tooling fixes discovered during verification

The user invited tools that help future agents. The reproduced detached-job
failure justified a separate shared-tool proposal: the existing supervisor
lock gives a run-specific liveness signal even when `/proc` and numeric PIDs
come from different namespaces. A shared nonblocking probe avoids mistaking
other readers for the worker, and a protected reread handles completion during
the check. Actual owner loss remains unclean and nonresumable. The isolated
proposal passes 33 focused tests, including 18 new cases; identical tests on
unchanged source produce 13 failures and 20 passes. The first incomplete-fixture
run is retained separately. This is not a full-suite pass, a new platform
port, or an applied shared change. Details are under
`checks/process-liveness-proposal/`.

The first task-delta replay also exposed a zero-exit Git skip from `WORK/`
inside a Git root one directory above it. Source-file verification caught the
failure; the subsequent no-tests result was retained and not counted as
success. The standalone `apply_verified_delta.py` now validates the explicit
Git root, derives the required path prefix, binds the patch and all before/after
file hashes, rejects skipped patches, and writes its receipt exclusively
outside the source tree. A review found that a receipt could otherwise replace
a newly created source file; its actual failing revision and regression are
retained. The final five guard/application cases pass on small original-source
copies. No source in the selected task delta changed during these tooling
iterations, so its completed solve and fresh-copy tests remain current.

## Current parametric extension — review-cd5ac0967088d57b

Status: **proposed task-local prototype, not selected or approved**. Production
`generator.py` remains byte-identical at
`fa8f82d356825247d12033364a9c6de885922c2d3829e2de75399d211516cae6`,
and the canonical one-step Racket authority remains `b9f9e9bda3f3`.

The prototype under `workspace/parametric/` adds one episode-level parameter,
`projection_reach = one_step | to_boundary`, selected once and held fixed across
all demonstrations and queries. `one_step` is the exact canonical default.
`to_boundary` preserves the same unique rare color, source-shape erasure, and
occupied row/column extents, but continues each extent projection to the canvas
boundary. This transfers only the public-evaluation task `142ca369` idea that an
object-derived projection can continue beyond a local marker; it does not claim
verified lineage or measured difficulty.

Exact retained evidence contains one hard episode per setting, each with four
demonstrations and four distinct queries. Racket matched all 16 intended labels,
all 16 rival executions matched the Python mirror, every demonstration refuted
the other setting, every query changed under the rival, and the canonical
setting replayed all six supplied canonical pairs. Public files omit parameters,
seed, program, and query answers; their names are SHA-256 of exact visible bytes.
The writer sorts by public ID and rejects duplicate visible payloads before any
write. See `workspace/parametric/evidence/manifest.json` and
`checks/parametric/48bda9528e71-projection-reach.json` in the return.

A bounded adversarial pass exercised the maximum supported 16+16 pair counts,
a forced 256-attempt duplicate retry schedule, exact-integer public colors,
private-field ID invariance, visible-input ID sensitivity, and duplicate-public
preflight. No defect was found in that scope. Limits: only two retained Racket
episodes and one maximum-count seed were sampled; this is not an all-seed proof.
The next useful action is maintainer review of the extension's semantic value;
only after an explicit selection decision should any production parametric API
or broader seed census be considered.

## Native completion design

Extend the existing `one_step` / `to_boundary` proposal through the native
adapter path, retaining its two semantic settings. Factor the current projection
loops into a shared pure kernel; the legacy validated API keeps its original
contract, while the native validator extends the same occupied-shape grammar to
square 5..30 canvases. The native default returns the exact selected canonical
bytes rather than the historically rebuilt equivalent program.

Construct independent complete six-demo/four-query banks before count slicing.
Three mandatory demonstrations teach concave extents, both projection reaches,
rare-color inference and foreground zero; large queries use substantial shapes
through 30x30. The causal intermediate is the per-row/per-column extent table,
not merely a color. Replacing it by global bbox endpoints on a concave shape
must change the executed spatial output with the palette and reach fixed.
Focused regressions, protected finite shortcut review, guarded inventory update,
native qualification, causal replay and single-query public projection complete
this proposal. Existing evidence remains historical and owner acceptance pending.

### Native color-selector teaching repair

Independent review screened 11 plausible selectors at two seeds and both reach
settings, then confirmed all eight candidate cases through protected Racket.
Three shortcuts fit every original demo but failed a query: fewest interior
cells by color; most monochrome components with numeric tie-breaking; highest
numeric fully enclosed color. The minimum query exposed the first two because
its outer color has zero interior cells and each color has one component.
Exact programs, labels and source snapshots are retained under
`checks/48bda9528e71/self-review-*`.

Strengthen the existing three examples while retaining the first cross unchanged:
use a thin-arm notch for the second with rare9 at its only interior cell and
common0 elsewhere; put the third demo's common9 patch wholly inside the occupied
shape and use rare0. The first demo keeps its fully enclosed common0 below the
nonzero rare color, so repairing the highest-enclosed shortcut does not introduce
the opposite lowest-enclosed shortcut. All four query roles stay unchanged.
This retains frequency inference, enclosure, center/bbox confounds, concavity and
clipping while making the wrong selectors observably fail. The three exact
observed rivals plus the opposite enclosure guard are part of the native audit
menu; no extra demo is added.

### Final dominant-color geometry repair

The first color repair passed 123 focused tests and refuted all eight retained
color-selector cases, but the expanded protected audit found four query conflicts
for geometry derived only from the most frequent foreground color. Every demo
still let that color supply the full occupied outline. Preserve that failed
`audit-final` evidence and repair only the third demonstration: keep its occupied
mask and orientation, retain the five-position RNG draw, select one of those
positions as rare zero, color all other interior cells nine, and leave the
boundary in the third color. Nine now has 35 versus 34 or 54 versus 41 common
cells and is wholly enclosed. Its geometry must give different extents from the
whole shape. Both common counts still exceed the unique rare count.

The first two demonstrations and all twelve query inputs at seeds 0, 17 and
`2**63-1` remain byte-identical. Fifty-three sampler regressions pass, including
the earlier color-selector refutations and the newly observed geometry shortcut.
Final protected checks use new `complete` destinations so intermediate results
remain attributable to their actual source revisions.

### Native reviewer readiness

Final source checks pass 129 focused tests, all 112 protected shortcut comparisons
are refuted by demonstrations, all eight original findings are replayed with
unchanged queries, and 20 maximum-seed labels match protected Racket. The guarded
native inventory replaces the inherited manifest while retaining historical
evidence. Native qualification passes four jobs across both settings and seeds
0/17 with 40 Racket evaluations. Two bbox-extent counterfactuals, one per reach,
are constructed and freshly replayed. Sixteen single-query public views verify;
all three saved-output corruption probes reject their temporary copies.

This is reviewer-ready for the exact returned prototype. Owner qualification and
fresh acceptance remain pending after integration; training admission is false.
The independent final review found no concrete remaining issue within the stated
source/evidence scope. Finite checks do not establish universal identifiability
or measured learning benefit.
