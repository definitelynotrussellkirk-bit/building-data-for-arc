# Working notes: 2a41d6b25262

## Baseline

Selected baseline generator SHA-256:
`fecbb297db0f5fed0c4de20effe39ed9dcfd1f6c07b187d4f4d7ab89cbb0907e`.
No prior return was treated as verified evidence; the selected packet baseline
was measured directly.

The before battery recorded 7 green, 2 advisory, and 3 failed stages
(`checks/before/checks/2a41d6b25262_before_battery_summary.json`). The blocking
failures were:

- missing `RULE_HASH`, singleton/inert axis metadata, and unprobed controls;
- ordinary texture values that were byte-identical to the default draw, with
  invalid negative fixtures overlapping the ordinary texture domain;
- 38,622 override findings across 44,010 draws, led by `grid_h`/`grid_w` being
  advertised but ignored, absent draw provenance, incompatible difficulty/
  variant combinations, and unknown override keys being silently accepted.

The old distribution still reduced template geometry to two four-cell pairs.
That allowed a solver to learn pair/size identity rather than normalized XOR.
The original self-check also returned success for declared invalid textures,
which hid malformed examples instead of validating the actual task domain.

## Repair

The generator was replaced with a rule-pinned, deterministic connected-
polyomino sampler. It now:

- validates one marker and one connected component for each source color;
- requires overlapping but non-identical normalized supports;
- samples 3–8-cell shapes from the complete fixed-polyomino bank that fits in a
  4×4 box;
- randomizes translated three-slot layouts and source/anchor reading order;
- exposes only literal, observable `grid_h` and `grid_w` controls;
- rejects unknown, mistyped, out-of-range, or invalid difficulty arguments;
- preserves canonical 10×15 support in every band through scheduled anchors;
- declares semantic rivals for union, intersection, one-source copying,
  post-XOR cropping, and canonical count-pair lookup;
- emits generated counterexamples to every declared rival and checks complete
  lessons through `lesson_identifiable`.

The canonical rule was already correct and remained untouched.

## Test-first findings retained

The initial task-local regression suite failed 61 cases on the selected
baseline (`checks/task_tests_red.log`). The first candidate passed the focused
suite, but the 600-draw semantic replay exposed two rare edge-clipping aliases:
a wrong union and the canonical size lookup could be clipped down to the true
answer. Two exact pinned cases were added before the anchor placement was
changed to reserve the whole 4×4 normalized-template footprint
(`checks/edge-clipping-red.log`, `checks/edge-clipping-green.log`).

The standard battery then went 12/12 green, but a stricter cyclic-query probe
found 75 ambiguous rotations among 1,500 when the only uncropped-origin witness
was moved into the query. A 100-lessons-per-band regression was added first
(`checks/cyclic-lesson-red.log`), then a second schedule residue was made a
guaranteed origin witness. The repaired cyclic test and reusable JSON probe now
cover 300 lessons and all 1,500 query rotations with zero declared-rival
survivors (`checks/cyclic-lesson-final.json`).

The workspace probe initially failed only in the portable copied runtime because
its subprocess lacked the packet runtime import path. That real portability
failure is retained under `checks/task-tests-final/`; the tool now bootstraps
`src` and `shared/runtime`, and the replacement portable snapshot passes 74/74
under the protected Racket runtime (`checks/task-tests-final2/`).

## Final measured source

Final generator SHA-256:
`f4a6fc32980f47689a65ebe40a6a6a114f1f2a7fc539e4dedeebf3726446f3bd`.

- final battery: 12/12 green, no advisory/failure
  (`checks/after-final-source/checks/2a41d6b25262_after_battery_summary.json`);
- semantic gate: 295/600 strict canonical-like, all 3 canonical inputs accepted,
  geometry and set-operation witnesses 600/600, origin witness 387/600, all
  180 sampled rival claims verified, 12/12 smoke lessons identifiable;
- overrides: 9,900/9,900 draws accepted over 110 cases with zero findings;
- diversity: 300 pairs, 100% unique inputs, 99% unique outputs;
- task-local portable tests: 74/74 passing;
- cyclic lesson probe: 300 lessons, 1,500 rotations, zero ambiguity/errors.

## Limits

This remains a finite declared-rival evaluation, not a proof of unique
induction. Shapes are deliberately bounded to connected 3–8-cell polyominoes
inside 4×4 boxes, colors and object counts are fixed to the canonical task, and
outputs always fit a reserved 4×4 footprint. Those restrictions preserve the
selected rule's task domain while keeping lessons small and checkable, but they
do not represent every mathematically possible XOR-stamp input.
## Current reviewer considerations

Source SHA-256: `f4a6fc32980f47689a65ebe40a6a6a114f1f2a7fc539e4dedeebf3726446f3bd`.

# Decisions — 2a41d6b25262

## Scope and authority

I treated the selected generator and its teaching distribution as defective,
not the rule. The canonical Racket authority already implements independent
normalization, symmetric difference, and stamping correctly, so its file and
hash `75fe298a62dd` were kept unchanged. No prior return was accepted as proof;
the packet baseline was measured directly.

## D1 — Replace fixed pairs with connected-polyomino geometry

**Decision.** Sample two distinct, overlapping normalized connected shapes of
3–8 cells, each fitting a 4×4 box, from a deterministic shape bank; transform
and place them independently.

**Why.** The baseline effectively offered two four-cell pair identities. A
solver could associate a small catalog entry or ordered count pair with an
answer instead of learning normalize → XOR → stamp. A connected-polyomino bank
adds genuine geometry variation while keeping enumeration and exact tests
tractable.

**Rejected alternatives.** Random cell masks were rejected because they would
frequently be disconnected and make the object interpretation noisy. Very large
or unbounded shapes were rejected because lesson generation, exact override
support, and exhaustive edge checks would become expensive without adding a
necessary canonical behavior. Fixed hand-authored shape tuples were rejected as
another memorization surface.

**Known limit.** This does not cover disconnected source masks or connected
polyominoes larger than eight cells or wider/taller than four.

## D2 — Keep canonical semantic roles fixed

**Decision.** Keep exactly one red (`2`) source, one green (`3`) source, one blue
(`1`) marker, and cyan (`8`) output on zero background.

**Why.** Color roles and object counts are semantic in the selected rule, not
nuisance variables. Varying them would require a changed rule or a new role-
encoding convention and could produce examples outside the canonical task.

**Rejected alternative.** Palette permutation was rejected because the Racket
rule names the canonical colors. Advertising a palette axis would therefore be
either false or a rule change.

## D3 — Expose only literal observable controls

**Decision.** Public `AXES` contains only `grid_h` and `grid_w`, with exact
integer domains. Unknown keys, booleans, out-of-range values, and invalid
difficulties raise errors.

**Why.** The baseline's broad axis surface contained singleton values, aliases,
dead texture controls, and ignored dimensions. Removing fake controls is safer
than preserving an API that cannot be observed in the grid.

**Rejected alternative.** I did not add shape-index, profile, or palette controls.
Those are internal curriculum choices and would create difficult joint-support
promises without a user need.

## D4 — Use a scheduled teaching distribution

**Decision.** Use four profiles: the three canonical ordered-size signatures
`(4,4)`, `(5,4)`, `(5,5)`, plus a leading-offset profile. Schedule profiles by
sample index, with two residues guaranteed to preserve a normalized-origin
witness.

**Why.** Canonical-size support is required, but repeating only canonical
signatures would preserve Q1's lookup shortcut. The leading-offset profile
refutes post-XOR cropping. The second guaranteed origin witness was added after
R3 showed that a single witness can disappear when rotated into the query.

**Rejected alternatives.** Pure independent random sampling was rejected because
witness frequency does not guarantee complete lesson coverage. A one-witness
period was tried and rejected by the retained 75/1,500 cyclic ambiguity failure.

## D5 — Reserve the complete 4×4 output footprint

**Decision.** Constrain anchor jitter so every possible normalized-template
offset remains in bounds, rather than relying only on the realized XOR support.

**Why.** The first candidate allowed clipping to erase cells that distinguished
wrong rules. Exact R2 cases showed union and canonical-size lookup becoming
accidentally answer-equivalent at an edge. Reserving the full source-template
footprint removes that alias at its cause.

**Rejected alternative.** Checking only the final XOR cells would still let
union-only cells or rival-specific lookup cells clip away. Padding the output
would change canvas semantics.

## D6 — Make shortcuts executable contracts

**Decision.** Declare callable rivals for union, intersection, red-only,
green-only, cropped XOR, and canonical ordered-size lookup; declare witnesses,
canonical shortcuts, and lesson competitors; validate exact demonstration
outputs in `lesson_identifiable`.

**Why.** Prose claims are not enough. Executable rivals let the semantic gate,
shared census, and cyclic probe measure whether a wrong rule survives each
lesson. The strongest canonical-fit rival is included rather than selected after
the fact.

**Rejected alternative.** A fixed list inside the probe was rejected. The probe
iterates `LESSON_COMPETITORS` so later contract additions are automatically
covered.

## D7 — Separate the independent oracle from production helpers

**Decision.** Put an independent task statement and canonical reader in
`workspace/reference_probe.py`; use it in tests instead of deriving expected
answers from the generator's own mirror.

**Why.** A production implementation and its mirror can share the same error.
The independent support-normalize-XOR-stamp code gives task tests a distinct
failure surface. Racket remains the selected authority and is checked separately.

## D8 — Add an all-query-rotations tool

**Decision.** Build `workspace/cyclic_lesson_probe.py`, covering 100 lessons per
band and all five query positions, with replay seeds, profiles, input hashes,
canonical shortcut fit, declared-rival survivors, and hook findings.

**Why.** The production census checks its native four-demo/one-query orientation.
R3 and audit A2 both demonstrate that this can miss a unique witness placed in
the query. The companion is intentionally task-local because shared support does
not yet expose cyclic rotation; F1 proposes that shared change.

## D9 — Preserve failures and avoid unrelated refactoring

The baseline red suite, clipping failures, cyclic failure, portable bootstrap
failure, interrupted battery receipts, and audit findings remain under `checks/`.
Only selected-task files were edited. Audit targets were measured and reported,
not patched.

## Failure modes and interpretation

- Finite declared rivals do not establish universal identifiability.
- Exact duplicate input hashes are measured, but semantic equivalence under
  translation/rotation is not deduplicated.
- The task domain intentionally excludes malformed colors, missing objects,
  disconnected templates, and out-of-bounds stamps rather than teaching them as
  ordinary examples.
- Generated approval/training admission is unchanged; green review checks do not
  themselves approve the generator.

## Current bounded audit assessment

`review-9ed9662fed3056ba:v0001` found no actionable in-domain defect on source `f4a6fc32980f47689a65ebe40a6a6a114f1f2a7fc539e4dedeebf3726446f3bd`. This is reviewer-reported evidence for the tested examples and controls only. The current assessment and minimal receipts are in `evidence/current-audit-assessment.json`; its domain limits remain relevant.
