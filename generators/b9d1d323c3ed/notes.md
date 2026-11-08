# Current notes — b9d1d323c3ed (original ARC 28bf18c6)

## Rule and domain

On a zero background, find all cells of the sole nonzero color, crop their
bounding box including internal zeros, and concatenate two copies horizontally.
Canonical Racket authority remains `8d4993ada3e1`; no rule or base authority was
changed by review `review-045026c983176de4`.

Version 3.1.0 retains input dimensions 8–18, all nine foreground colors, seven
layouts, three box-size categories and three placement biases. The bbox has
both sides at least two and a background cell, and the canonical output is
smaller than the input in both dimensions. All documented override combinations
remain constructive. Exact observable controls are height, width and color.
Seed must be an exact integer (negative integers remain valid); sample_index
must be an exact nonnegative integer; difficulty is None/easy/medium/hard.
Boolean/numeric/string coercions are rejected before sampling.

## Current repair and reversed decisions

Prior source `a585f0ff7647f713be4614830381f48c8f573150b7df5e9df90c9775b1a5d008`
was accepted in `review-408b9b2cd3a7a519:v0001`. Its notes/index supplied context,
not fresh measurements. This review found 39 strict-scalar warnings despite
33 passing inherited tests. Explicit call validation repairs those gaps.

Previously, every crop had occupied upper-left and lower-right corner anchors.
That guarantee made three of four canonical occupancy masks impossible to
sample. The new construction draws its layout first and fills only missing
top/bottom/left/right extrema at keyed random positions. A solid rectangle
loses one random cell; both sides are >=2, so its extent cannot shrink. The
explicit 2×2 diagonal layout remains available. Scattered sampling has positive
support for every non-full spanning binary mask. Finite evidence found all
four supplied masks among seeds 0–1502, sample_index=0, fg_layout=scattered;
actual Racket outputs were checked for those witnesses.

The six-axis surface, 8–18 size limit, background zero, single nonzero color,
non-solid crop and output shrinkage are retained. Broader sizes, solid crops,
multicolor inputs and uniform pattern sampling are not claimed.

## Lessons and rival scope

Even indices select canonical 8×8 / 3×3 boxes; odd indices select non-3×3 boxes.
`LESSON_SCHEDULE_PERIOD=2` makes the existing alternation explicit. Three demos
and one query from four consecutive accepted default draws contain two variable
boxes, retaining a witness after any one-query rotation. Arbitrary overrides
or filtering still require the lesson hook/resampling.

`fixed_3x3_crop` fits all four canonical pairs and remains the named canonical
shortcut, semantic rival and lesson competitor; these are aliases for one
rival. A 2×2 diagonal witness has actual output 2×4 versus rival output 3×6.
Fresh evidence records 300 lessons / 1,200 rotations with zero ambiguity against
this rival (1,079 unique inputs). Both start residues in each band at seed 0
also passed: six lessons, 24 rotations, nine unique inputs. These finite checks
do not establish unrestricted identifiability.

## Proposed parametric extension

`workspace/parametric/prototype.py` adds episode-wide axis={horizontal,vertical}
and copies={2,3}. Default horizontal/two returns exact canonical Racket text.
Alternatives preserve object identification, tight crop, zeros and identical-copy
concatenation. Selected-generator inputs are filtered to bbox sides 2–10 so all
four possible outputs fit 30×30. Four distinct pairs include two variable-box
witnesses. All four executed parameter settings and all 16 query rotations pass
the retained bounded checks, also testing four fixed-3×3 Python diagnostics.
Public challenges contain only demonstrations and input-only queries.

This is a separate prototype, not a production API or approved variant. The
exporter runs from a library checkout through review.py; episode/execution
helpers also support the isolated task-test runtime.

## Evidence and tools

Final generator SHA-256:
`c6b2755a958c938be5ffd0ef8806a43cb3024283d1ef4db446bde70ea01b0901`.
The return retains 12/12 green strict battery stages and 71/71 task tests with
zero skips. The first after battery omitted its schedule receipt and is retained
honestly; the final battery supplies it. No unresolved audit was listed for
this repair target at draw time. Acceptance/training admission remain separate.

Use `workspace/coverage_probe.py` for canonical occupancy witnesses,
`workspace/parametric/README.md` for runnable variant commands, and
`counterexamples/review-045026c983176de4.json` for exact examples. The inherited
reference probe and prior evidence remain intact.

## Current owner source and evidence limits

Accept literal scalar guards and bbox-extrema construction without forced occupied opposite corners. VERSION3.1.0 and canonical identify/crop/repeat rule unchanged,although intended sampling support changes. Reviewer reports12/12 battery,71 tests repeated fresh353/96910-file runtime closure,all4 canonical occupancy masks found in1503 scatter draws,300 lessons/1200 rotations/1079 unique inputs clean;6 fixed seed starts/24 rotations/9 unique inputs clean. Inherited33 tests unchanged;new31 canonical+7 prototype tests. Proposed horizontal/vertical x2/3 copies yields4 Racket-labelled episodes/16 identifiable rotations,exact horizontal2 canonical source. Authoring outputs stay<=30;canonical canvases8-18,prototype crop sides2-10. Arbitrary overrides/filtering do not inherit default lesson guarantee. No variant/training approval. Owner checks source hashes and public/private projection statically;reported labels/tests are not owner reruns.
## Current reviewer considerations

Source SHA-256: `c6b2755a958c938be5ffd0ef8806a43cb3024283d1ef4db446bde70ea01b0901`.

# Decisions — review-045026c983176de4

## D1 — Nearby transformation parameters first

Axis (horizontal/vertical) and copy count (2/3) change actual executed outputs
while preserving the original object roles, crop bounds, zeros, and identical-copy
concatenation. Cosmetic reskins teach less; unrelated added operations would
alter the reasoning structure. The default returns exact canonical Racket text,
verified against all four labeled canonical pairs.

A hash of one integer episode seed selects a complete setting once. Explicit
settings also apply episode-wide, never pair-by-pair. Labels and all four
parameter alternatives execute through Racket. Four fixed-3×3 Python diagnostics
are separately labeled rivals, not authorities. Four complete 3-demo/1-query
episodes and all 16 holdouts passed; variants remain proposed.

## D2 — Common legal domain and evidence separation

Selected-generator inputs are filtered to crop sides 2–10, giving all settings
outputs <=30×30. This avoids a rival comparison that wins only through overflow.
Bounded rejection retains actual accepted/rejected indices and reasons, with a
512-draw failure cap. Four distinct accepted pairs alternate 3×3 and variable
boxes, keeping a variable demonstration after every query holdout.

Private evidence includes settings, programs/hashes, seeds, labels and rivals.
Public files have opaque names and contain only demos and input-only queries.
The exporter runs in a library checkout; execution helpers support copied task
runtimes. Direct rule_wrap import initially lacked scripts.comment_solutions;
public prepare_runtime/run_process resolved it without shared changes. Its
failure remains in checks/parametric/initial-infrastructure.log.

## D3 — Reject invalid calls rather than coerce draw identity

Fresh defect lint found 39 warnings missed by the inherited 33 tests. New tests
reproduced bad seed/index/difficulty acceptance. Validation precedes RNG creation:
seed exact int (signed allowed), sample_index exact int >=0, difficulty only
None/easy/medium/hard. Existing override rejection remains. Version 3.1.0 makes
the changed deterministic stream explicit. Legal signed-seed controls remain tested.

## D4 — Reverse mandatory corner anchors

The previous upper-left/lower-right anchors guaranteed extent but excluded three
canonical masks. A 4,096-seed red test demonstrated missing support, backed by
the structural anchor argument. The replacement builds the requested layout and
fills only missing extrema at keyed random positions. A fully filled rectangle
loses one cell; sides >=2 ensure its extent remains. Randomly replacing the
whole mask was rejected because that would erase layout semantics.

The reusable coverage probe found canonical train0/train1/train2/test0 masks at
seeds 1502/580/2/4, sample_index=0, fg_layout=scattered. Total scanned range was
0–1502 (1,503 draws), not four independent uniform samples. Actual Racket output
checks cover these four generated witnesses plus a minimal 2×2 diagonal rival
counterexample. The probe and exact inputs remain task-local.

## D5 — Retain size/override contract and expose the schedule

The six-axis surface, dimensions 8–18, zero background, single nonzero color,
non-solid crop and output shrinkage are retained. Larger dimensions would add
unrelated compatibility work; 21–30 input support is not claimed. Difficulty
reweights sizes while every documented exact dimension stays available. The
final profile floor has 27/60 exact/envelope hits and nonzero support in all bands.

Canonical/variable alternation is unchanged. Declaring period two allows complete
start-residue checks at one fixed seed. The first after battery lacked the
receipt and warned; separate seed-0 enumeration passed six lessons/24 rotations,
then final battery consumed that receipt and passed 12/12. The declaration and
required-rotation policy were kept rather than relaxed.

The 300-lesson census with 3 demos/1 query found no ambiguity against the one
fixed-3×3 rival, including all 1,200 rotations. Its three declaration namespaces
are aliases, not independent rivals. Arbitrary overrides/filtering require the
lesson hook/resampling; the default consecutive-window argument does not cover them.

## D6 — Preserve audit, solve and approval boundaries

The blind task finished before generator/reference inspection. The post-repair
solve used final generator bytes and visible-only material during that phase,
with earlier exposure declared yes. Both matched 3/3 visible examples in one
revision; private queries remain unscored. No negatives were manufactured.

Audit b8aea529acfd is bounded No issue found after fixed-seed schedule and actual
Racket checks. Audit 77871cecd343 reproduces a retained schedule-correlation lead:
54 default/5 canonical fits and a valid override refutation. No audit target was
edited. Acceptance of this main repair must not clear the separate open finding.

Only assigned task code/tests/notes/tools/counterexamples enter the source patch.
Canonical rule, shared APIs, catalog and approval records are unchanged. The
supplied return builder and fresh runtime-closure replay provide the final handoff;
focused tests run in that copy's own environment. No full-library suite result,
universal induction guarantee, or training admission is claimed.
