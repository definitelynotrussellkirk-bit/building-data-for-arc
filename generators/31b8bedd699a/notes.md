# Current notes: 31b8bedd699a

## Selected proposal and authority

Version `3.0.0`, generator SHA-256
`2f1d4a9496deb459cdf33397713daefd85e02ed53b5e1a979ee9439c3843f4dc`.
Assignment baseline `2.0.1` had SHA-256
`71f99d654314cc6b40b07c0374e33a02ec33cdefa537e865f999e1f9c55d78ac`.
No task-specific prior review or associated-note lead was available in this draw.
The original intent of unsupported controls is unknown.

The canonical Racket rule (`ca3b9033626d`) is unchanged: select non-solid nonzero
monochrome four-connected components, compare retained top-left coordinate
ranges, choose vertical iff row range is strictly greater, stably sort on that
coordinate, and emit one fixed 4×4 hollow token per frame. Ties are horizontal;
colors may repeat. The domain validator additionally requires complete outlines
or solid rectangles, dimensions 3–8, 2–5 frames, 0–3 solids, valid integer cells,
and a background-cell gap between boxes.

Only the active `racket_target.target_code` strings in the two assignment-pinned
base solution aliases were synchronized to the existing canonical text. Archived
`raw_code`, unrelated fields, the canonical ledger, and both audit targets remain
unchanged. Authority synchronization is not a change of rule semantics.

## Repairs and reversals

- **M1 — validator:** the previous component-count check admitted solid-only,
  single-frame, broken-outline and invalid-cell inputs. Exact component support,
  object counts and separation are now checked; independent geometry regressions
  cover invalid mutations and valid canonical examples.
- **M2 — controls/placement:** silently ignored controls, narrow override bounds
  and silently dropped solids were replaced with four observable exact integer
  controls. All joint tuples of canvas sides 15–30, frames 2–5 and solids 0–3 use
  constructive placement. Retired keys are `anchor_corner`, `asymmetry_force`,
  `palette_size`, `position_bias`, `palette_kind` and `texture`; they now raise
  `ValueError`. `None` continues to mean no override. This intentional interface
  change is why the version is 3.0.0.
- **M3 — semantics/teaching:** the old summary's crop/unspecified-order account was
  replaced with fixed-token normalization and exact top-left/tie semantics.
  Six canonical-fitting shortcuts, fourteen lesson competitors and eleven
  executable disagreement witnesses are declared. Reference labels remain Racket.
- **M4 — schedule reversal:** the first v3 draft passed the 139 geometry tests but
  supplied insufficient redundant evidence against including solids in the axis.
  An exact six-pair counterexample is retained. The repaired broad vertical and
  horizontal scenes each place a solid that flips the all-object axis while
  preserving the frame-only axis, so that witness survives any single holdout.
  Real broad-profile difficulty draws replaced initially inactive bands.

## Lesson policy and measured scope

The default phase cycle is canonical vertical, broad vertical, canonical
horizontal, broad horizontal, canonical tie, broad tie. `EXAMPLES_NEEDED=5` and
`LESSON_SCHEDULE_PERIOD=6`. The intended lesson uses five ordered demonstrations
and one query. Each of the six pairs may instead be held out, preserving the
order of the remaining five. Exact overrides remain valid inputs but are not a
promise that arbitrarily assembled custom lessons reproduce this witness policy.

All results below bind to the generator hash above. The final twelve-stage
battery passed with no advisories; its semantic stage checked 12 production
lessons and 72 holdouts with no ambiguities. A larger public Racket census checked
300 lessons (100 per difficulty band), 1,800 pair slots, 1,799 unique inputs and
1,800 holdouts with no ambiguity against the fourteen declared behaviors. A
fixed-seed-17 enumeration covered every start residue and every holdout across
three bands (18 lessons, 108 holdouts, 20 unique inputs), also with none. Independent
Python screening covered seeds 0–15, three bands, six starts and six holdouts:
288 windows / 1,728 holdouts / 310 unique inputs, with zero disagreements with the
independent oracle or ambiguous holdouts. Its public reference subset checked 18
inputs through Racket. These finite results do not prove universal induction.

All eight canonical ledger pairs (four unique examples) are accepted. The strict
all-4×4 fraction was 302/600; profile-floor matches were 31/60, with support in all
bands. The override gate completed 51,390 draws without findings. The local test
suite has 188 parametrized cases; the final return records its fresh patch replay.
Full evidence is retained in the assignment return under `checks/`; large JSON
files have lossless gzip copies and original-path/size/SHA mappings.

## Open support limitations — CR1 and CR2

The default phase choices correlate frame count and canvas width with output
orientation. An undeclared rule choosing vertical iff there are two frames and
canvas width is not 24 fits all default profiles. An eight-case Racket replay
confirmed all six default representatives fit and that the second canonical
training example plus a legal three-frame vertical override refute it. It is
not a canonical-consistent rival. Consequently the finite default-lesson result
must not be presented as evidence of transfer to the entire valid-input domain.

Most placements use a 3×3 lattice. Broad profiles repeat a frame color, while
canonical-style profiles with at least three frames require a numerically
nonmonotonic order. Distinct descending three-frame orders, including canonical
orders [4,3,2] and [3,2,1], are valid but absent from generation even with the
four current controls. Full canonical geometry/color-order coverage is therefore
not claimed. Future diversification should preserve redundant lesson witnesses
while restoring those omitted configurations; no Qwen performance gain was measured.

The assigned audits are findings-only and remain open on their separate targets.
Their retained reports belong to the assignment return, not this generator's
source approval. The exposed solve uses this exact generator hash and records
earlier authoring exposure; masked-query correctness remains unknown.
## Current reviewer considerations

Source SHA-256: `2f1d4a9496deb459cdf33397713daefd85e02ed53b5e1a979ee9439c3843f4dc`.

# Decisions — 31b8bedd699a

## Authority and scope

The pinned canonical Racket program, not the old prose summary, determines the
transformation. Four unique labeled examples appear twice in the canonical ledger;
the independent semantic probe verified all unique examples and four extra
witnesses through public `Catalog.apply`. The rule keeps nonsolid components,
compares their top-left spans, uses a strict vertical comparison, stably sorts and
normalizes each frame to 4 × 4. Six simpler alternatives fit all canonical examples,
so canonical agreement alone could not settle distribution design.

I retained the canonical rule and ledger byte-for-byte. The two assignment-pinned
active base-solution strings were textually divergent but behaviorally consistent
on canonical examples. Copying the selected canonical text into those active
fields resolves exact synchronization without revising behavior; historical
`raw_code` and other fields remain intact. Details: M5 and
`checks/authority-sync/receipt.json`. No source on either random audit target was
edited. No task-specific prior review lead was available for the main baseline.

## Input and control choices

| Choice | Original rationale / observed problem | Selected implementation | Rejected alternative / limit |
| --- | --- | --- | --- |
| Hollow-frame domain | Original prose intended rectangles but validation only counted components and accepted malformed examples | Exact complete outlines and solid rectangles, 3–8 per dimension, monochrome four-connectivity | Accepting arbitrary nonsolid shapes would broaden beyond the intended frame curriculum merely because Racket can label them |
| Frame and solid counts | Original placement could silently omit requested solids | Exactly 2–5 frames and 0–3 solids; independent pixel observer | Best-effort random placement would leave count failures seed-dependent |
| Canvas bounds | Difficulty-specific draw bounds contradicted advertised exact controls | Each exact side accepts 15–30 in every band | Clipping or silently interpreting controls as suggestions was rejected |
| Placement | Rejection attempts could exhaust without explaining an omitted object | Nine separated lattice slots support every legal joint control tuple; special two-frame contrast scenes supply semantic witnesses | The lattice is intentionally narrower than arbitrary legal placement; CR2 documents this transfer cost |
| Separation | Contact can merge same-color components or change their support | At least one background cell between every pair of bounding boxes, including diagonal neighbors | Merely disallowing occupied-cell overlap would not protect component identity |
| Colors | Distinct original colors conceal multiplicity; numeric sorting can imitate spatial sorting | Repeat colors in broad profiles; nonmonotonic numeric order in larger core profiles | These guarantees introduce omitted legal color sequences; they are documented under CR2 rather than called complete color coverage |
| Exact controls | Some advertised keys were dead or overridden by texture handling; original intent is unknown | Retain only `grid_h`, `grid_w`, `n_frames`, `n_solids`, observe them from pixels, reject unknown/retired keys and noninteger coercions | Retaining misleading knobs for compatibility was rejected; version 3 makes this deliberate interface break visible |
| Difficulty | First v3 draft produced identical bands | Use real `draw_int_diff` draws for broad sizes/counts; explicit controls still span their whole domain | Difficulty is not a rule change or a guarantee of measured solver difficulty |
| Canonical support | Original profiles missed canonical canvas/palette combinations, including seven colors with background | Three all-4 × 4 phases alternate with broad phases; `MIN_STRICT_FRAC=.45` | Strict acceptance and canvas/palette profile matches are not full support for every canonical spatial/color configuration |

The old summary's crop and vague-order explanation was replaced. Input frames may
be 3 × 3, 7 × 7, 8 × 8 or rectangular, but every output panel is still 4 × 4. The validator
checks a lawful superset of generated layouts; passing `self_check` does not mean
the sampler can emit that exact grid.

## Complete-lesson design and the failed first draft

`EXAMPLES_NEEDED=5` resolves the intended lesson to five demonstrations plus one
query. The six-phase cycle is canonical vertical, broad vertical, canonical
horizontal, broad horizontal, canonical tie, broad tie. Each ordinary six-pair
window contains evidence for normalization, repeated colors, correct tie handling,
both output orientations and spatial ordering. Every single-pair holdout is
checked, preserving the order of the remaining five pairs.

The first draft passed all 139 geometry regressions and individual witness
checks. It still had an ambiguous lesson: at seed 1/easy, start 4, holding out
position 2 (sample index 6) left demonstrations compatible with including solids in
the orientation range. The saved six-pair fixture records both predictions. A
bounded independent screen found 75 ambiguous holdouts among 1,728: 12 production
queries and 63 other rotations. The required public semantic smoke also found
two ambiguous rotations. These failures are retained as intermediate-source
evidence, not mislabeled as a failure of the final generator.

The repair deliberately positions one solid in each broad directional profile
so that the all-object span picks the opposite axis from the frame-only span.
Any extra solids must preserve that disagreement. Thus either broad scene can
teach the filtering-before-axis decision when the other is held out. This
addresses M4 at the lesson level, instead of resampling until a small green
sample happens to appear. Removing the rival, weakening required rotations or
treating correct individual labels as sufficient teaching were rejected.

Eleven witness predicates check actual rival-output disagreement, not visual
flags that merely suggest a witness is present. Six `CANONICAL_SHORTCUTS` are
verified against every usable canonical pair; all fourteen live competitors are
loaded dynamically by the retained probes. The Python mirror is diagnostic
only. Production labels, the main census and authoritative counterexamples use
the public canonical Racket path.

## Validation choices and practical limits

The red geometry tests failed 113/139 cases on the original generator. Final
focused checks pass 188 parametrized cases across two files. Source review found
one independent assertion gap for solid dimensions; it was closed and the 139
geometry cases rerun without changing generator bytes. The final fresh-patch
replay runs the complete 188-case suite on the exact packaged tests.

The battery covers the required twelve stages, but task tests are separate. The
final battery has 12 green stages and no advisories; override coverage comprises
571 case settings × 30 seeds × 3 bands = 51,390 draws. An additional arbitrary input is not certified by these counts. The strict subset was 302/600, and the
profile check matched 31/60 draws with support in all three bands.

The public large census materialized 300 lessons (100 per band), 1,800 pair slots
and 1,799 unique inputs, with zero production or rotated ambiguity. Its seeds use
the recorded SHA-based recipe and requested starts 0–99. A separate fixed-seed 17
census enumerated every start and holdout across all three bands: 18 lessons,
108 holdouts, 20 unique inputs. The independent Python screen used seeds 0–15,
three bands, six starts and six holdouts, totaling 288 overlapping windows,
1,728 holdouts and 310 unique inputs; it had zero ambiguities and an 18-input
Racket agreement subset. None of these denominators represents independent
generalization trials, and the checks establish only finite declared-rival results.

Exact-control inputs are constructively valid, but a custom override can replace
a contrast scene with a lattice scene and remove a particular witness. The hook
evaluates supplied demonstrations and queries honestly; it does not assert that
all arbitrary custom lesson assemblies are identifiable. Query rotations are
supported for the tested default six-pair policy. Different demo counts, mixed
override recipes or other export assembly policies require their own checks.

## Remaining distribution restrictions

CR1 is a concrete shortcut in default support: vertical iff there are two frames
and canvas width is not 24. It fits every default profile by source construction.
The retained public replay verifies six default representatives and two refuting
inputs: canonical train 2 and a legal three-frame vertical override. It does not
fit all canonical labels. This is a transfer limitation separate from the
fourteen-rival within-lesson result, and it is not hidden by that result.

CR2 follows from lattice placement, forced broad color repetition and forced
core nonmonotonic color order. Legal distinct descending three-frame outputs,
including canonical sequences[4, 3, 2] and[3, 2, 1], are excluded from generation.
Future work should vary count/axis/canvas combinations and restore omitted
orders while preserving redundant witnesses. This return accepts the smaller
teaching distribution as a scoped improvement over the broken baseline, not as
an exhaustive domain generator or proof of Qwen transfer. No training run or
model-performance delta was measured.

## Evidence and handoff decisions

Both solve phases followed the packet's visible-only policy and retained their
single genuine revision and frozen notes. The blind episode passed 3/3 visible
examples before rule inspection; the exposed final-source episode passed 5/5.
Both masked-query accuracies remain unknown. The logs are authored work summaries,
not captured token-level conversations.

The two assigned audits are findings-only and each has exact inputs, rival
outputs, authoritative Racket labels and a runnable reproducer. Their sources
were not repaired here. Reports and failed iterations are retained, and large
JSON evidence was losslessly compressed with original path/size/SHA mappings.
Only reproducible Python cache bytes were removed to relieve disk pressure; no
source evidence was removed. Fresh source extraction and runtime staging use
task-scoped temporary memory storage where needed, with actual paths recorded.

## Proposed parametric token-size / tie-policy extension (2026-10-23)

A task-local prototype now preserves the canonical frame-filtering, top-left-span
axis choice, spatial ordering and outline-normalization pipeline while selecting
`token_size ∈ {3,4,5}` and `tie_policy ∈ {horizontal,vertical}` once per episode.
The exact canonical default remains `(4, horizontal)` byte-for-byte; neither
`generator.py` nor canonical authority was changed. The other five programs are
materialized by checking and replacing only the two output dimensions, matching
quotient/remainder/border constants, and the strict tie comparison.

The ordinary retained episode has three demonstrations (tie, vertical,
horizontal) and four distinct queries (vertical, horizontal, tie, vertical).
The tie example identifies `tie_policy`, output dimensions identify `token_size`,
and all six settings use the same seven inputs. Protected Racket matched stored
labels and the independent Python mirror for 42 executions; all six public
projections mask query answers and use visible-payload-derived opaque IDs. Every
episode contains a query that refutes CR1's `n_frames == 2 and width != 24`
shortcut. Evidence is in
`checks/parametric-31b8bedd699a-token-tie-v1/manifest.json`.

The bounded adversarial pass generated and replayed 64 demonstrations plus 64
queries with 128 unique inputs, rejected strict-type/count boundary attacks,
preserved the public ID under 12 private-only mutations, changed it under all
three visible mutations, and rejected wrong-program, wrong-output,
duplicate-input, underidentified-demo and multiple-parameter-draw episodes.
Receipt: `checks/parametric-31b8bedd699a-token-tie-adversarial-v1.json`.

This remains a proposed prototype, not production approval or training admission.
Finite evidence covers six declared settings on one shared seven-input episode
and one seed at the authoring-count boundary; it does not establish uniqueness
against arbitrary programs or broaden the selected generator's support. A local
Racket body extractor binds the lambda parameter actually present in canonical
text (`grid` rather than assuming `g`), avoiding source rewriting while leaving
shared runtime untouched.

## Native token-size / spatial-order promotion (2026-10-25 reviewer return)

The retained native adapter is now `workspace/parametric/adapter.py`, with six
private settings from `token_size ∈ {3,4,5}` and
`order ∈ {ascending,descending}`. The exact canonical default is
`{"token_size":4,"order":"ascending"}` and preserves canonical Racket bytes
(SHA-256 `aec8493756257813cc44068749978fe481d201c5f2ad358212a15eb85266fd2d`).
Neither `generator.py` nor canonical authority changed.

The promoted family deliberately replaces the earlier tie-policy proposal. A
minimum-context audit found a real lesson hole in that design: for a vertical
selected tie policy, an `always vertical` rule could fit both visible examples
and fail a horizontal query. The repaired family keeps the canonical
input-dependent axis as Stage A and parameterizes spatial order in Stage B. Its
first two demonstrations expose vertical and horizontal axes, each sampled pair
separates all six settings, and the two-example prefix rejects eight named
fixed-axis/order/color/size rivals.

Stage A measures the top-row and left-column ranges of hollow frames and emits
`vertical` only when the row range is strictly larger; ties remain horizontal.
Stage B consumes that axis to choose both the stable sort coordinate and packing
orientation, then applies the episode-fixed ascending/descending order and token
size. The protected causal witness uses a qualified default-setting input with
`row_range=20`, `col_range=10`, and derived `vertical`; replacing that
intermediate with `horizontal` changes the final output from 16×4 to 4×16.
Construction and an independent replay both report `reviewer_replayed`.

The adapter supports independently prefix-stable 2–6 demonstrations and 1–4
queries. Four fixed query slots include a dense 30×30 five-frame/three-solid
case touching the top and left boundaries. A reusable source-bound audit sampled
32 seeds across all six settings (192 episodes), checked every supported visible
prefix and eight named rivals, and found zero dangerous ambiguities. The complete
task-local suite passed 232/232 under protected Racket. Native qualification
passed all six settings on seeds 0 and 17 with three demonstrations and four
queries per job: 12 jobs and 264 protected-Racket evaluations. The public
projection produced and reverified 48 one-query views with no structural
findings.

Current evidence:

- source inventory: `workspace/parametric/evidence/manifest.json`
  (SHA-256 `97f8b015e16b325afe0ee4a360552d57b587e8bdb8d0817e7ebb106dcfdcc227`);
- qualification: `checks/31b8bedd699a/qualification/qualification.json`;
- execution: `checks/31b8bedd699a/qualification/execution.json`
  (SHA-256 `22cbf6ed344551292cf41e83e268242a21cbf845a192d221f2f0cb00e41052d9`);
- causal witness: `checks/31b8bedd699a/witness/witness.json`;
- independent witness check: `checks/31b8bedd699a/witness-check.json`;
- finite audit: `checks/31b8bedd699a/native-audit.json`.

This status is reviewer-ready and owner-pending. The evidence is finite, does
not prove uniqueness against arbitrary programs, and does not claim owner
acceptance, training admission, or measured model-learning benefit.
