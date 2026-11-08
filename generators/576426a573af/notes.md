# Working notes: 576426a573af

## Current external review — review-c91c8b8b50062268

This follow-up changes only proposed-prototype public export identity, its
regressions and documentation/evidence. Canonical generator version 2.2.0 and
SHA-256 `d49ae2e612265752d5ce3cec5982071c6c6d96bb35183a47dff37719fd2eb0be`
are unchanged. The current public-identifier section below describes the repair.
All other detailed repair counts, old check paths and the final handoff record
below are inherited from `review-314653c4a38c2ca6:v0001`; they are retained as
history and are not new measurements of this review. Current measurements and
commands are in the current return's REVIEW.md and RESULTS.json.

**D9 — replace ordinal public names with visible-content identities.** The
previous batch writer used SETTINGS-order ordinals, revealing private settings.
Random IDs would lose deterministic replay; removing batch export would remove
useful functionality. Exact public-byte hashes provide stable identity without
adding hidden information. Sorting writes prevents enumeration-order leakage;
private-only mapping preserves author traceability. The input grammar and all
canonical sampling decisions D1–D8 remain unchanged.

## Current rule and contract

Version **2.2.0** keeps the canonical Racket transformation unchanged: overlay
the original grid on its up/down reflection. Every original nonzero cell stays
in place; only an original zero can be filled from its mirrored partner.
Different nonzero mirror partners therefore retain their original colors.
The authority pin remains `RULE_HASH = "892d64eecd2e"`.

Generator SHA-256:
`d49ae2e612265752d5ce3cec5982071c6c6d96bb35183a47dff37719fd2eb0be`.

The exact controls remain `grid_h` in 4–18, `grid_w` in 3–18, and
`fg_palette_size` in 3–6. Unknown keys and invalid types/ranges raise. Seeds
and sample indices must be actual integers, excluding booleans; indices must
be nonnegative. Negative integer seeds remain supported. Every generated input
retains zero background, every requested foreground color, and at least one
singleton mirror orbit. Odd-height middle rows stay blank.

## Distribution and teaching schedule

Every four consecutive sample indices cover four roles. The declared complete
sampler subcycle is `LESSON_SCHEDULE_PERIOD = 8` because canonical slots
alternate between authentic anchors and stochastic stacks.

| Role | Construction and purpose |
|---|---|
| `canonical_bottom` | Default 10×4 bottom-anchored sources with 3–4 foreground colors. Alternate canonical slots preserve a recolored training geometry; other slots draw stochastic anchored stacks. |
| `top_only` | A connected top-anchored source plus a connected patch of 2–4 different-color mirror partners, retaining at least one top-only singleton. |
| `bidirectional` | Singleton source orbits alternating between halves teach both copying directions. |
| `conflict` | Arbitrarily placed 2–4 conflicting mirror orbits plus singleton sources teach repeated original-cell precedence. |

The conflict count is drawn from 2 through `min(4, occupied_orbits - 1)`.
This preserves a singleton even at 4×3 and realizes an exact six-color request.
Connected top conflict placement avoids adding several disconnected endpoint
fragments to the anchored profile; the separate conflict role retains arbitrary
locations. When a wide override has fewer occupied cells than columns, the
anchor row uses contiguous columns so the source remains connected.

Two roles retain the canonical shape/palette envelope by default. Only
`canonical_bottom` is strict-canonical, providing one strict example per four
consecutive demonstration slots. Its strict foreground envelope remains 8–14
because the three canonical inputs contain 11, 12, and 14 foreground cells.
Overrides may move a role outside that canonical profile.

## Decisions and relevant reversals

**Teach multiplicity in both conflict-bearing roles.** Version 2.0.0 placed
exactly one conflict in each. Audit `review-c7594485a8c40a6c:v0001` against
source `5154ac7b3bf20cd1b86784f04f997d3d9d9b03d00b6b98c8388c237a0f2439ca`
identified a canonical-compatible rival that preserves only the first conflict.
The current sampler repeats multiple conflicts in both roles, declares
`preserve_first_conflict_only` alongside `bottom_to_top_only` and
`mirror_wins_conflicts`, and links it to the executable
`multiple_conflicting_pairs` witness. Adding multiplicity only to the dedicated
conflict role would leave a leave-one-out lesson without that evidence.

**Preserve meaningful source morphology.** The first multiplicity repair
(version 2.1.0) passed focused semantic tests but failed two full-battery
heuristics. Its 120-input generated component median rose from the baseline's
2.5 to 4.0, partly because the top profile's mirror endpoints were scattered.
The connected-subset repair reduces that final diagnostic median to 2.0 while
keeping the broad conflict profile. The generic marker warning means exactly
one monochromatic singleton was absent from a small sample; it does not establish
a special marker role. A controlled version-key experiment showed that warning
could also appear without the multiplicity change.

**Add bounded authentic anchors.** Every other canonical slot (12.5% of the
unoverridden eight-index schedule) now uses one of the two actual **training**
input geometries and its equal-color partition under an injective palette
relabeling. The three-color request selects the three-color training pattern;
the four-color request selects the four-color pattern. This path runs only at
10×4 with a compatible palette. Other shapes or palette sizes use the existing
stochastic canonical construction and honor all controls. The other canonical
slots and all three teaching roles remain generated. No canonical query/test
geometry is used. This preserves authentic color-region structure rather than
tuning random seeds until an exact-support heuristic happens to pass. The final
60-input diagnostic sample has seven one-singleton examples and no disjoint
structural signature features. See `checks/repair/morphology-diagnosis.json`
and `checks/repair/morphology-final.json`.

## Reproduction and focused evidence

`counterexamples/conflict_multiplicity_lesson.json` retains four exact baseline
demonstrations and the lawful constructed two-conflict audit query. The rival
fits all four demonstrations and differs on the query. All five labels were
re-executed through canonical Racket in
`checks/canonical-witness/lesson-racket.json`; the separate verification receipt
binds that result to the retained lesson. The baseline did not generate the
constructed query.

`checks/repair/commands.json` records exact commands, working directories,
return codes, and source hashes. New regressions were exercised before their
fixes: 81 failures/1 pass for multiplicity and scalar defects, 21 failures/7
passes for morphology support, and two failures for probe provenance. The
canonical focused suite passed **235/235** in `green-final-regressions.log`
before the additional portable-layout regression. The final official portable
task-test stage passed **266/266**, including the separate prototype tests, in
`checks/task-tests-portable-fixed/result.json`.
Intermediate results, including the failed first full battery and the prior
probe-count assertion, are retained separately rather than relabeled final.

The first portable task-test collection failed because the snapshot contains
both execution-layout dependencies and repository mirrors under `shared/runtime`.
Three test bootstraps selected the mirror before the probe's public loader
selected the execution layout, so the loader correctly rejected a cached module
from the other tree. The four task-local bootstraps now prefer execution-layout
dependencies. A fresh-process dual-layout regression reproduced that failure
before the fix and now passes. The loader's source-tree guard is unchanged;
no module cache is cleared. The original failure remains at
`checks/task-tests-final/result.json`, and the regression's red receipt is
`checks/repair/red-portable-runtime-layout.log`.

The reusable `workspace/curriculum_probe.py` checks the independent audit rival
even if a future source removes its declaration. At seed 17, starts 0–63, and
default/easy/medium/hard bands, `checks/repair/curriculum-portable-final.json` records
**256 ordered windows, 1,280 leave-one-out rotations, and 1,024 per-query checks
in four-query lessons**, with no failures. Each eight-input lesson is distinct;
its four demonstrations alone refute all three checked rivals. The 284 distinct
band/index draws represent 233 unique grids, with conflict counts 0:144, 2:51,
3:49, and 4:40. Overlapping windows and cross-band anchors are not treated as new
unique inputs. The baseline rival survived every corresponding context.

The probe compiles the selected generator through the public portable loader
and records the returned executed-byte hash and source path. It does not hash
a later live file or trust timestamp bytecode caches. Real temporary-copy tests
cover both failure modes and the staged dual-layout import order. Probe labels use an independent Python oracle;
production Racket labeling, the portable battery, and production lesson censuses
remain separate evidence in the review results.

## Limits and separate prototype

The three finite rivals and bounded probes do not prove unique induction against
every hypothesis. Conflict multiplicity is sampled only at 2–4 in the two
conflict-bearing roles; larger counts remain outside generated support. The
schedule is cyclic rather than IID. The maximum side remains 18: 30×30 support
was considered but not added to this bounded canonical repair. This is a
sampling limit, not a semantic limitation claimed for reflection.

The original-family extension under `workspace/parametric/` is a separate
prototype. Its proposed parameters, Racket programs, and examples do not change
canonical authority or grant approval. Existing approvals and prior green logs
are not checks of these new bytes, and source edits do not implicitly resolve
the audit index. Imported associated notes remain in
`evidence/associated_notes.jsonl`.


## Current proposed prototype public identifiers

Review `review-c91c8b8b50062268` corrects the prior fixed-SETTINGS ordinal leak.
Batch public paths now use `episode-<SHA256 of exact public challenge bytes>`.
The shared projection includes demo inputs/outputs and query inputs only; private
settings, seeds, reference programs, extra metadata and query answers cannot
influence identity. Batch directories are created in sorted public-ID order.
Duplicate visible payloads are refused before creating output. The single
`public/challenge.json` path remains compatible. Caller-supplied ancestor paths
remain the caller's responsibility when exposing files.

The actual Racket-backed regression first failed on the old ordinal and then
all 36 focused tests passed. Four seed-17 settings retain two demonstrations
and four distinct queries each; all 16 queries are identified from demos, all
six inputs per episode are distinct, and canonical parity is 3/3. Evidence and
exact commands are in `checks/parametric/public-identifiers-review.json` and
`checks/parametric/public-identifiers-corrected/` in the current return.

The current `workspace/parametric/evidence/manifest.json` inventories corrected
source hashes. Its prior exact bytes are archived alongside it. Historical
ordinal-named exports and the source-bound pending finding remain unchanged;
this external correction does not rewrite the historical finding's status.
The extension remains proposed: no variant approval, production-parametric API,
canonical authority, or training-admission policy was changed.

## Current reviewer considerations

Source SHA-256: `d49ae2e612265752d5ce3cec5982071c6c6d96bb35183a47dff37719fd2eb0be`.

# Design and implementation decisions — 576426a573af

## Plan and constraints

Goal: return a verified task-local repair and a reusable parameterized episode
prototype for the original training:f25ffba3 family. Work in the independent
extraction; the original ZIP and immutable assignment remain the baseline.
The task's existing Python generator, shared Racket bridge, portable task-test
runner, census and delta packager define the implementation interfaces.

- [x] Verify packet and finish the pre-repair visible-only blind solve.
- [x] Run the before battery; retain its scalar-validation warnings.
- [x] Add the axis/precedence prototype under workspace/parametric, with default
  parity, Racket labels, independent train/test counts and public/private outputs.
- [x] Add regression evidence and repair repeated-conflict coverage and invalid
  call scalars while preserving canonical authority and profile support.
- [x] Verify the combined source with the battery, portable task tests, declared
  rival census, every declared schedule start, and a four-query production episode.
- [x] Finish the post-repair visible-only solve; perform both drawn audits.
- [x] Build a compact delta and replay it in a fresh independent checkout.

## Approaches and decisions

D1. Use task-local prototypes with exact Racket programs. Adding a global rule API
would exceed the assignment; changing the canonical rule would erase its lineage.
The selected design uses two bounded settings: vertical/horizontal reflection
and original/mirror precedence. The default is vertical/original. These choices
change the executed transformation while retaining the mirror-pair relationship.
They are reviewer-proposed variants, without production approval or training
admission. They were chosen from the packet's authoring brief, not specified by
the user separately.

D2. Repair the documented conflict-multiplicity gap within the existing four-role
curriculum. Retain the canonical bottom anchor and add redundant multi-conflict
witnesses so leaving one pair out cannot remove all precedence evidence. A named
count-limited rival makes the former gap executable. Keep existing size bounds
(height 4..18, width 3..18); 30x30 support is outside this bounded repair.

D3. Reject bool, float and string seeds/indices rather than accepting coercion.
Seed remains an integer (negative integers allowed); sample_index must additionally
be nonnegative. The baseline defect lint reported 33 accepted-invalid scalars.
New tests must fail against the baseline and pass against the repaired source.

D4. Preserve unknowns: checks cover declared rivals and finite samples, not all
possible hypotheses. Query correctness in both authored solve records remains
withheld for maintainer scoring. Audits are findings-only and do not edit targets.

D5. Preserve authentic training morphology in a documented subcycle. The first
repair (v2.1.0) fixed conflict multiplicity but increased fragmentation: the
120-draw diagnostic median object count rose from 2.5 to 4.0, and the strict
battery also flagged absent canonical color-component signatures in its finite
sample. Changing only the version string and hence the random stream did not
resolve this. The final v2.2.0 uses connected top stacks and a connected subset
of reflected conflict cells. One of every eight default sample indices uses
one of the two original TRAIN input geometries under an injective nonzero color
map. The other canonical-bottom slot remains stochastic; the other three roles
remain varied. No canonical query geometry was copied. The final diagnostic
median is 2.0 over the same 120-draw design, with canonical singleton-component
support 7/60; the full defect and distribution gates pass. See
checks/repair/morphology-diagnosis.json and morphology-final.json.

The 12.5% anchor share makes canonical support explicit instead of relying on
rare random color partitions. It deliberately trades some cross-episode variety
for coverage. Exact incompatible shape or palette requests take the ordinary
lawful role path; they are never silently rewritten to fit an anchor. Recoloring
changes color labels while preserving equality classes. Expanding every sample
into an authentic template was rejected because it would eliminate the broader
teaching cases. Removing structural gates or tuning their seeds was also rejected.

D6. Declare the complete schedule and attach its receipt to the strict battery.
The four teaching roles retain a canonical-bottom/top-source/bidirectional/
conflict cycle, with an eight-index authentic/random anchor subcycle. Four
consecutive demonstrations contain redundant conflict witnesses. Production
checks hold the next pair out as the query; rotation checks hold out each of the
five labeled pairs once, preserving remaining order. The 300-lesson census is
100 lessons in each of easy/medium/hard, with deterministic hashed seeds and
consecutive requested starts 0..99. It materializes 1,500 pairs, 1,491 distinct
inputs, and 1,500 query rotations. Separately, declared-period enumeration covers
all eight starts at seed 0 across the three bands: 24 lessons, 120 rotations,
32 distinct inputs. Both pass against the three named rivals. The first v2.2
battery lacked the attached schedule receipt and correctly remained non-green;
checks/after-verified attaches the source-bound census and passes all 12 stages.

D7. Treat source identity as part of reusable-tool correctness. Independent
review reproduced a timestamp-bytecode cache mismatch in the old probe loader,
and a second mismatch after editing the source following import. The probe now
uses reviewer_support.load_selected_generator with find_root and retains the
returned executed-source hash/path. Both regressions failed before the repair
and pass afterward. It reads live declarations rather than a copied rival list,
reports overlapping windows separately from unique inputs, and checks four
queries against common demos. The required portable tests additionally exposed
a dependency-mirror import conflict; that failure is retained rather than being
mistaken for a generator error or hidden by weakening the source-tree guard.
Four task-local bootstraps now prefer the manifest's execution layout before
the repository mirror. A fresh-process dual-layout regression first reproduced
the failure, then passed with the repair; the official portable suite passes
266/266 tests. Final code/probe identities are retained in
checks/repair/final-portable-source-manifest.json and its source-matched
checks/task-tests-portable-fixed/result.json receipt.

D8. Keep the parametric extension separately proposed. Its vertical/horizontal
axis and original/mirror precedence settings are fixed once per episode. Inputs
do not encode a setting-specific random stream, and query sampling is independent
of demonstration count. A protected three-color/one-zero quartet makes the four
rules distinguishable from demonstrations. This is an intentionally informative
prototype grammar, not the full rule-valid support or a calibrated difficulty
distribution. Canonical parity is 3/3 actual Racket outputs. The four seed-17
settings each retain two demos and four distinct queries, with 16/16 queries
identified from demos; a seed-29 sampled setting adds one demo and four queries.
Public artifacts omit settings, programs and query answers. No global API,
canonical rule, approval metadata, or training admission was changed.

## Scope and remaining support limits

The repair closes the concrete first-conflict-only teaching gap and validates
strict call scalars; it does not claim to exclude every possible count-limited
rule. Conflict-bearing roles now draw two through four conflicting orbits, so
rules that behave correctly for four conflicts but fail beyond that remain
outside the measured support. Heights remain 4..18, widths 3..18, foreground
palette sizes 3..6, and odd-height center rows remain zero. These are deliberate
bounded-generator limits; the separate prototype provides larger query shapes
through 30x30 without silently changing production support.

The authentic anchors make some exact grids recur across bands: the final
300-lesson census contains 1,491 distinct inputs among 1,500 pairs. Every retained
four-query production episode has eight distinct inputs. Fixed schedule order
and the prototype's protected quartet can themselves be learned; the finite
rival tests establish teachability only against the hypotheses they execute.
Neither authored solves nor these checks establish human difficulty or a model's
learning behavior. The prior audit return review-c7594485a8c40a6c:v0001 remains
an unresolved historical record; this patch adds fresh evidence without changing
its status or implying maintainer acceptance.

## Review focus

Minimal 4x3 grids with six foreground colors must retain a singleton, all colors,
and multiple conflicts. Odd-height center rows must stay lawful. Every cyclic
lesson start and leave-one-out position must retain witness coverage. Four-query
lessons must identify each query from demos alone. Prototype public files must
omit chosen settings, Racket source, and query outputs. Final replay must test the
actual transported files with its own runtime environment.

## Evidence and final outcomes

The final canonical generator is v2.2.0, SHA-256
`d49ae2e612265752d5ce3cec5982071c6c6d96bb35183a47dff37719fd2eb0be`.
The original Racket authority SHA-256 remains
`892d64eecd2edc24785002c9575a773a25810505cb6a2b52212f3429dc977a22`.
All expected failing regressions, intermediate battery failures, and the earlier
source-bound solve are preserved. Final aggregate and fresh replay outcomes are
listed in REVIEW.md and RESULTS.json; those files distinguish completion from
finite support limits and proposed variants.

Final handoff: the source patch was applied to a fresh 365-file declared runtime
closure from the original 103,286-member ZIP. All 12 changed-file hashes matched,
and the fresh environment passed all 266 portable task tests. The extraction
was intentionally partial; no full-repository test claim is made. The source
patch identity is b97db84bff0cd2d14f2713524f7cc5eb5f51cd1cb4d1898bb4fbd50305f43b36.
