# Current notes: fa3550d200a0 / training:414297c0

## Rule and domain

The unique modal nonzero color identifies a rectangular canvas. Extract outside
multicolor objects with eight-neighbor connectivity. Match each object's unique
nonzero, non-2, non-canvas marker to the same-colored canvas marker; translate
the complete object to that marker and return the stamped canvas crop. Ignore
objects whose marker has no canvas match. Color 2 is a fixed payload symbol.
Canonical Racket semantics remain `af9e935761ad`; the canonical program and
approval records are unchanged. Saved labels are executed by Racket, not the diagnostic
Python prediction or rivals.

The validator accepts the supplied canonical inputs and the broader lawful
object domain. Sampling requires a modal filled canvas, unique marker matches,
isolated outside objects, two to five matched pieces, zero or one decoy, and
unclipped, marker-preserving stamps. It does not sample markerless objects,
duplicate marker anchors, clipping, ambiguous canvas colors, or marker overwrites.

## Sampling and teaching decisions

Version 4.0.0 used only marker-centered radius-one, cardinally connected
templates. Version 5.0.0 adds endpoint pieces and diagonal connections. This
addresses the exact-source leads in audits `review-54679fb53aee003c:v0001`
and `review-48f831f8020a3b47:v0001`: a 3×3-window rival fitted every canonical
pair, and a four-connected rival fitted every generated template. The former
is declared in `CANONICAL_SHORTCUTS`; both and crop-only are lesson competitors.
The retained audit records still require an explicit maintainer disposition;
source changes do not silently resolve them.

Even sample indices include a cardinal endpoint and a diagonal-only piece.
Their stamped footprints are protected from overlap so another piece cannot
hide the distinguishing payload. Other pieces may still overlap payloads.
Odd indices sample all ten templates. Rotations/reflections, positions, canvas
side and marker colors vary. The unchanged count cycle is 2,3,4,5 matched pieces
and 1,0,1,0 decoys. Three consecutive demonstrations precede queries; every
four-pair cycle contains two explicit examples distinguishing each tracing
rival, which also supports holding out any one pair in the measured rotations.
The declared period four describes scheduling, not seed-independent grids.

The old 20..30 × 24..30 size distribution had poor canonical-profile support.
The new 16..30 × 18..30 range mixes canonical size/color anchors with broad,
difficulty-weighted draws. A profile means height, width and distinct-color
count together; it does not claim matching canonical canvas geometry. The
default count cycle has six or eight colors, so the seven-color profile needs
an explicit count choice. Both 30×30 and meaningful small rectangular inputs
remain supported. Seeds must be exact integers; sample indices must also be
nonnegative, with booleans and coerced scalars rejected.

## Exact controls and limits

All advertised axes are recovered from output pixels by `observe_overrides`.
There is one coupled size limit: `rect_w <= grid_w - 10`, reserving two
three-column piece lanes, one-cell gaps and borders. An impossible explicit
pair raises `ValueError`; a lone rectangle-width override conditions the width
draw on compatible values. Canvas height/width remain 6..12. Thus wide canonical
canvases, including width 15 and a 12-wide canvas in an 18-wide input, remain
validator-supported but outside this finite sampler. The three-number profile
mixture does not remove that limit. Outside shape bounding boxes are at most
3×3, with marker-relative radius up to two; longer shapes remain untested.
The two-lane outside layout is another finite-support restriction.

`workspace/probe_canonical.py` retains source-bound baseline/final checks,
actual-Racket comparisons, declared-rival results, joint override boundaries
and four-query evidence. `tests/test_review_contract.py` covers the concrete
scalar, geometry and teaching regressions. The full lesson census is finite
evidence against the declared competitors, not unique identification against
all possible programs.

## Separate proposed extension

`workspace/parametric/` proposes a quarter-turn parameter fixed for an entire
episode. Turn zero preserves exact canonical program text; alternatives rotate
piece offsets about their marker before stamping. Its sampler filters for
fit and nonoverlap across the tested settings, and its demonstrations must
distinguish settings before query generation. It exposes independent demo and
query counts and exports sanitized public challenges. This is a prototype,
outside canonical approval and without any claim of training admission.

## Authority repair and remaining inherited gate

The baseline authority-sync check found formatting differences between selected
`target_code` copies and canonical `program_solution`; normalized hashes agreed
and execution parity passed. Initial review treated these shared paths as
outside scope. Final inspection corrected that interpretation: both selected
authority files are explicitly bound by ASSIGNMENT and allowed by the return
contract. The reviewed `authority-sync --selected-only` proposal was applied
through the supported command. Only those selected strings now match exact
canonical formatting; archival `raw_code` and the canonical ledger are unchanged.
Application receipts and recovery originals accompany the return, along with
a new full battery under `checks/after-synchronized/`.

The required isolated task-test stage also stops at the unchanged inherited
fixture's fixed `__file__.parents[1]` canonical-data path. Its byte identity is
preserved as required. `workspace/proposals/portable-frozen-fixture.patch`
provides a non-applying migration to the public root/data-loading helpers;
the separately tested migrated copy passes the five original tests. All 39
new authored tests pass separately. Neither result converts the unchanged
required stage into a pass; the maintainer owns that fixture migration.


## Current maintainer intake limits

The accepted repair retains reviewer-reported needs-attention status: latest battery11/12, override killed with exit137 after94000draws, unknown cause; earlier identical-source112410draw completion is separate individual-stage evidence, never an aggregate pass. Frozen fixture portable-data-path preflight remains blocked and unchanged;39 authored and5 migrated-copy proposal tests reported pass separately. Quarter-turn prototype stays proposed/unapproved:16 reported3demo+4query episodes,64queries; static inspection found visible-content-derived public names and independent counts, without owner execution. Capacity-preflight feedback remains deferred under owner direction. Source-bound limit capsules: `generators/fa3550d200a0/evidence/aggregate-failure-4b0eec4e2abff891/manifest.json`, `generators/fa3550d200a0/evidence/frozen-fixture-blocker-4b0eec4e2abff891/manifest.json`.
## Current reviewer considerations

Source SHA-256: `c5a3a7e69f0ae05f1408fde8a7ee0fed8a10e196726efdd1438ec70b805a6a73`.

# Decisions for fa3550d200a0

Assignment `review-4b0eec4e2abff891`; original family `training:414297c0`.
Baseline version 4.0.0, generator SHA-256
`dbd7e8b5a46571f83a63aa4e2b8abbae691931512ff21c7775a76d5badbda782`.
Final version 5.0.0, SHA-256
`c5a3a7e69f0ae05f1408fde8a7ee0fed8a10e196726efdd1438ec70b805a6a73`.
Canonical normalized rule hash `af9e935761ad` is unchanged.

## D1 — Separate a meaningful rule parameter from canonical sampling

The original-family assignment prioritizes parameterization. Before canonical
repair, we chose one small spatial parameter: clockwise quarter-turns 0,1,2,3
of each outside piece about its marker before stamping. Object extraction,
canvas identification, color matching, unmatched-piece filtering and crop
composition remain the same. Turn 0 returns the exact canonical program text;
alternatives change its two relative-coordinate expressions. No catalog kind,
runtime API, selected rule, or approval record changes.

Rejected alternatives were a cosmetic palette permutation, which would not
change the executed transformation, and an unrelated second operation that
would weaken the relationship to the parent family. The chosen parameter is
fixed once per episode; demonstrations intentionally teach that hidden setting.
The prototype rejects inputs unless all four rotations fit and matched target
footprints are disjoint under each setting. This is a documented narrower
prototype domain, not a change to canonical validation.

`workspace/parametric/prototype.py` provides a bounded builder;
`workspace/parametric/verify.py` exports and replays exact programs, episodes,
source bindings and sanitized challenges. Demo selection executes the four
candidate settings and must eliminate competitors before query generation.
Query labels do not select demos or remove rivals for another query. Separate
demo/query controls default to 3/4, with no input duplication in an episode.
Exhaustion retains its trace and fails rather than shortening the episode.

Evidence: 16 complete episodes, 112 accepted pairs and 64 query labels across
seeds 17/73, all four settings, default sizes and exact 20×20/30×30 suites.
All exports and fresh program replays completed. Rotation-domain rejections
were 256/80/76 in the three suites; the largest observed attempt count was 41
against a 500-attempt cap. The counts across settings reuse comparable inputs
by design; they are not 112 globally unique inputs. See
`checks/parametric/SUMMARY.json`, each suite's manifest, exact programs and
`checks/parametric/command-records.json`. The extension remains **proposed
prototype**, not approved synthetic training data or measured model progress.

## D2 — Repair the two exact-source support gaps

The current audit index supplied leads `review-54679fb53aee003c:v0001` and
`review-48f831f8020a3b47:v0001`. Their source hash matches this packet's selected
baseline. We reproduced rather than assumed their findings. Baseline actual
Racket checks cover 38 inputs: 8 canonical appearances/4 unique inputs,
28 generated/boundary inputs, and 2 handmade separating controls. The 3×3-window
rival fits all canonical and generated cases. The four-connected rival fits
all 28 generated cases but only 2/8 canonical appearances. No baseline generated
label error was claimed; the problem is teaching support.

Prior choice → new choice: only centered radius-one cardinal templates → retain
those templates and add a three-cell endpoint line and a diagonal-only piece.
Even indices force both types among the matched objects, with arbitrary
rotations/reflections. Their target footprints are protected so overlapping
payloads cannot hide the distinguishing cells. Other pieces retain payload
overlap support, and odd indices randomly choose from all ten templates.
Copying more canonical grids or changing the reference was rejected: neither
addresses the generator's systematic omission while preserving variation.

Declare the actual 3×3-window, four-connected and crop-only competitors. Only
the 3×3-window rival is a `CANONICAL_SHORTCUTS` claim because it fits every usable
canonical pair. The two tracing witnesses are checked against actual Racket
labels by the shared semantic gate. The Python `diagnostic_stamp` is explicitly
a diagnostic and never supplies saved training labels.

Three consecutive demonstrations are declared. The existing count cycle stays
2,3,4,5 matched pieces with 1,0,1,0 decoys; the teaching period is four. Two forced
witness inputs in each four-pair cycle support any one held-out pair. The main
consumer evidence remains ordered production; rotations are reported separately
as diagnostics, not a universal policy assertion. A 300-lesson census at 100 per
band found no declared-rival ambiguity in 300 production contexts or 1,200
rotations, with 1,200 distinct materialized inputs. The complete compressed
report and its hash manifest preserve every case. The semantic battery also
enumerates all four start residues in each band at fixed seed 0:12 lessons,
48 rotations, 10 unique grids across overlapping windows/bands. None of these
finite results establishes all-seed or all-hypothesis identifiability.

## D3 — Restore canonical-scale support without obscuring size limits

Baseline size ranges 20..30×24..30 made three canonical size profiles impossible.
Its required 60-draw census had exact support 1/60 and envelope support 7/60,
including zero exact hits in medium and hard. The new range is 16..30×18..30.
A keyed mixture favors compatible canonical height/width/color profiles in
every band while retaining broad difficulty-weighted draws. Exact overrides
remain first-class keyed draws; a fixed rectangle width conditions the grid
width draw rather than being clipped after sampling.

The required final 60-draw profile census records exact hits 9/20,8/20,8/20 and
envelope hits 18/20,15/20,13/20: pooled 25/60 exact and 46/60 envelope, zero crashes,
warnings or canonical rejections. A separate seed 0..19 probe measures 32/60 and
41/60; these are different populations and are not pooled or substituted.
Exact 30×30 and 20×20 boundary inputs are separately exercised through Racket.

We retained the practical two-lane outside placement and 6..12 canvas dimensions.
Its explicit coupling is `rect_w <= grid_w - 10`. Incompatible exact requests
raise `ValueError`; 192 of 640 boundary tuples are intentionally rejected.
The remaining 448 are distinct, lawful and reproduce all requested controls.
This is preferable to silently shrinking a canvas, dropping objects, or merely
padding duplicated queries. The final Racket probe has 98 accepted records:
8 canonical appearances, 60 defaults, 28 representative lawful joint edges and
2 handmade controls; all 98 outputs agree with the independent diagnostic.

Limits remain explicit: default counts have six/eight colors, so the seven-color
canonical profile requires count overrides. A 15-wide canonical canvas and a
12-wide canvas inside an 18-wide input remain validator-supported but outside
sampler geometry. Shape bounding boxes stop at 3×3 and marker-relative radius 2;
the two-lane layout also limits placement support. Profile success does not
erase these restrictions or imply general scaling/composition mastery.

## D4 — Exact call semantics

The defect linter reproduced 24 invalid scalar acceptances in the baseline.
Seeds now require exact integers, and indices require nonnegative exact
integers. Booleans, numeric strings and floating-point coercions are rejected.
Negative integer seeds remain allowed; negative sample indices do not. Existing
integer override bounds already rejected coercion and are preserved.

A new scalar regression was first run against the unchanged source and failed
on `seed=True`, as expected (`checks/session/red-scalar.json`). All 15 focused
repair tests pass after repair. The first after battery also exposed a metadata
format mistake: appending the coupled constraint to `AXES.rect_w.valid` prevented
the linter from parsing 6..12. We moved the explanation into a separate
`constraint` field, retained the failed battery, and reran on final bytes.
No execution semantics changed in that metadata correction.

## D5 — Independent four-query support

The exact canonical command is:

```sh
WORK/.venv/bin/python review.py run ../.venv/bin/python -m arcpuzzles generate \
  fa3550d200a0 --count 1 --seed 17 --test 4 --allow-unapproved \
  --out ../checks/canonical-probe/four-query/episode.jsonl
```

It produces 3 demonstrations and 4 queries from accepted indices 0..6, with 7
distinct inputs and zero rejected draws. All 7 labels were re-executed through
canonical Racket. The shared demos refute all three rivals; each query is checked
independently without borrowing another query's answer. Editing the generator
invalidates the baseline approval, so the research command correctly requires
`--allow-unapproved`; no approval hash was refreshed. Prototype commands and
separate 3/4 counts are in its README and executed command records.

## D6 — Preserve the packet's frozen boundaries and make blockers reviewable

The final required task-test stage stops at preflight because the unchanged
baseline fixture hardcodes a source-depth-dependent canonical-data path.
Its hash remains `381842af7a5c27e575f1cfcd7218db1b755bdf7fb9c47b9e9f0ce6c25204839f`.
The packet explicitly forbids changing that fixture. We supplied a small
non-applying migration patch and ran its five original tests in a separate
copy; 5/5 passed. All 39 new authored tests pass separately. Those passes do not
replace the required failed stage. Fresh patch replay independently reproduced
the same frozen-fixture preflight failure and passed all 39 authored tests.

The inherited authority-sync gate failed exact-text identity for two selected
`target_code` fields. Their normalized identity matched the canonical rule and
execution parity passed. Initially we retained a non-applying proposal, wrongly
interpreting all shared paths as outside the selected-task scope. Final inspection
of ASSIGNMENT's baseline and the unchanged return allowlist established that
these two task-specific authority files are explicitly permitted. We reviewed
and applied `checks/authority-sync-proposal.json` through the supported command;
the exact receipt and recovery originals are in `checks/authority-applied/`.
Only those two fields changed, to exact canonical formatting. Canonical program
bytes and archival raw code remain unchanged. The final authority-sync gate
passes under `checks/after-authority-complete/`. That full battery completed
with 11 green stages and one failure: override exit 137, last reported progress
94,000/112,410 draws. The outer exit is 124, internal exit is 1 and the runner
records `timed_out: true`. Its 203-second duration is below the roughly
3,928-second allowance; the cause of the kill remains unknown.

The earlier `after-synchronized` attempt completed all 112,410 override draws
with zero findings and warnings, before a later checkpoint write failed. Its
entire 257-file runtime manifest and recorded settings match the latest run.
`checks/individual-stage-evidence.json` records the successful individual stages
without combining them into an aggregate pass. The interrupted attempt and
refused resume remain separate evidence. The frozen fixture and latest failed
aggregate are both completion gates, so the acceptance brief remains
**needs attention**. Repeating the already completed override population again
would not resolve the frozen-fixture restriction; the preserved receipts make
the outstanding work concrete for the maintainer.

## D7 — Honest solve, audit and replay evidence

The separate blind solve was finished before authoring inspection: one revision,
3/3 visible pairs, earlier exposure no, reference consulted false. The post-repair
solve was prepared from final c5a3 bytes and finished with one revision, 3/3 visible
pairs, earlier exposure yes and no reference reopened during solving. Both
masked-query scores remain unknown. No artificial failed solve was invented.

The two drawn audits are findings-only and keep their own source-bound evidence;
they do not alter audited targets or clear any prior audit. Independent code
review found no substantive issue in the reviewed generator/prototype/probe
sources, while explicitly distinguishing static review from execution evidence.
The handoff replay applied the exact task delta from the original ZIP and
matched all 14 changed files. Its 360-file declared runtime closure is explicitly
partial relative to 103,286 original files. Following temporary-memory
exhaustion, relocation verified all 370 resulting source files and the exact
Git root. A newly created local Python environment and bundled Racket runtime
ran all 39 authored tests successfully; runtime imports were checked to remain
inside that checkout. The required isolated task tests still stop at the frozen
fixture preflight. These source, test and resource outcomes remain distinct in
`checks/fresh-replay/verification.json`. The final source patch matches the
replayed candidate bytes at SHA-256
`4974f746900d840093cf721d2e1c2414a2ea6fb79c93e0717a5b07ae633136d1`;
report and evidence additions do not change it.

## D8 — Admit the task-local quarter-turn family as native-ready evidence

The retained prototype material is now exposed through a native adapter with
`quarter_turns` in `{0,1,2,3}`.  The default `0` resource is byte-identical to
the canonical rule.  Inputs are sampled from the production generator, while
claim labels are computed by a separate Python transform and then replayed by
the protected Racket worker.  Full six-demonstration/four-query pools are built
before slicing, so demo/query counts are independent and prefix-stable; the
fourth query is an exact 30x30 stress case.

Fresh focused plus retained tests passed 56/56.  Native qualification covered
four settings, seeds 0 and 17, three demonstrations, four queries, and 128
protected-Racket evaluations.  The public projection exported 32 sequential
views; first-turn checks passed 48 private-field invariance mutations and eight
positive controls.  The reviewer-replayed causal witness uses a turn-one
qualified episode and the canonical turn-zero program as a wrong-intermediate
counterfactual: marker-relative piece offsets are extracted, rotated, then
stamped at the corresponding canvas marker.

This is finite source-bound evidence, not universal identifiability, owner
acceptance, measured training gain, or training admission.  The sampler remains
limited to lawful production scenes that separate all four rotations, and the
Python oracle's correctness is bounded by the recorded all-setting Racket
parity and qualification jobs.

## D9 — Repair the inherited portable task-test fixture and bound Racket startup

The current round's first portable task-test attempt reproduced the inherited
fixed-parent canonical-data failure.  Unlike the earlier packet that retained a
proposal only, this assignment permits changes anywhere under the selected task
home, so the test now uses `find_root`, `canonical_pairs`, and
`load_selected_generator`.  Its five focused tests pass in both the repository
and copied-runtime layouts.  The adapter parity parametrization also shares one
module-scoped protected-Racket bridge rather than starting four independent
bridges; this removes an unnecessary startup surface without reducing the four
settings checked.  The final source-bound portable gate passes 79/79 in 11.64s.

These are test-harness repairs only.  They do not alter generator behavior,
canonical rule bytes, adapter outputs, or the already-qualified source binding.


## Current parametric reconciliation

The accepted quarter-turn family from review-45e0523d83232945 remains current. Independent return review-c5bd8cc3551df1d6 declares the same four settings; its exact source, execution and causal evidence are retained in workspace/proposals/review-c5bd8cc3551df1d6/decision.json for sampler comparison. This proposed repeat does not replace or expand current acceptance.

## Current repeated-return reconciliation

Preserve the exact four incumbent quarter-turn programs/default. Alternate complete episodes between the incumbent broad sampler and the complementary larger multi-piece/decoy profile bank; retain the 30x30 query and shuffle query order independently of setting. The first return is the exact incumbent semantic contribution; repeated rotations are aliases, not extra settings. Evidence: `evidence/reconcile-13/`. Private native qualification, fresh private acceptance and a fresh accepted episode passed. Live owner publication and training admission remain separate.
