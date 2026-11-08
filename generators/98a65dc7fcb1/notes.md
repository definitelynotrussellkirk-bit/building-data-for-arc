# 98a65dc7fcb1 — review-0a0a7f531c095e30

Version 2.0.0; source SHA256 `29c6a2f1df57fcddb81e12cde94dbbb1fa793848c5acf46eb4e4b91ca09645eb`; canonical rule hash `7878169c3c87`.
Input-only generator. Canonical Racket supplies all production labels.

Normal schedule (sample_index%4): clean, clean, contrast, attached. Every
unoverridden contiguous three-demo window sees counterexamples to cardinal-only
fill, ignoring perimeter colors, overwriting an occupied center, and whole-
component 3x3-box filling. Four tested rivals are not all possible algorithms.
Clean slots retain canonical 7x9/9x9/9x10 two/three-ring scenes.

Ordinary controls: grid_h/grid_w integer5..18; n_rings integer1..6;
n_decoys integer0..6; palette_kind default/warm/cool/varied; texture
default/contrast/attached. Exact counts use separated 4x4 reservations and
structured capacity failures. Unsupported old names now fail loudly.
`observe_overrides` counts this emitted grammar, not arbitrary connected scenes.

Negative textures no_rings/filled_centers/missing_corner are explicit
self-check fixtures outside the normal valid texture domain. They honor
height/width, reject requested positive motif counts, and use fixed colors;
palette_kind is not effective in that diagnostic branch. Ordinary texture
counterexample guarantees do not apply when overrides remove required decoys.

Before: 4 battery failures and 2 advisories. After: all12 battery stages green;
59 explicit task-local tests pass. Matched probes use seeds0..99, indices0..7,
three bands: 2,400 draws and 1,500 overlapping three-demo windows. Every tested
rival survives all baseline windows and zero final windows. Exact outputs also
match Racket on all3 canonical pairs, 19,683 ternary3x3 grids and300 arbitrary
stress scenes. Details, hashes and reproducible tools: workspace/README.md and
the returned checks/*. No GPU/model-performance claims.

Tradeoff: cross-band clean anchors repeat. Globally unique inputs in the probe
are1,586/2,400 despite788/800 in each band. Content-deduplicate before dataset
splits. Negative-only lessons, large arbitrary connected layouts, and exhaustive
10-color neighborhoods are not claimed as ordinary generator coverage.

The bound base JSON active target text was synchronized to the unchanged
canonical program. Archival raw_code and approval fields remain unchanged.
## Current reviewer considerations

Source SHA-256: `29c6a2f1df57fcddb81e12cde94dbbb1fa793848c5acf46eb4e4b91ca09645eb`.

# Decisions and rejected alternatives

Main final source: `29c6a2f1df57fcddb81e12cde94dbbb1fa793848c5acf46eb4e4b91ca09645eb`. Decisions are reviewer explanations of the work,
not a transcript of hidden reasoning. The original notes were brief and did
not substantiate the original author's motivations; inferred rationale below
is identified as such.

## R1 — teach the complete predicate, not only the easy positives

Original behavior: clean, hollow, monochrome 3x3 rings only. Inferred motivation:
keep generation safe and close to the canonical examples. Evidence is the
source and baseline corpus; the author's actual motivation is unknown.
This leaves corners, color equality and the zero-center precondition unused
as discriminators. Recoloring more clean rings or merely increasing canvas
size cannot reject any of the four named rivals.

Choice: include a valid positive in every normal draw and add nearby-but-wrong
motifs. Missing corners distinguish eight neighbors from four; mixed corners
require color agreement; already-occupied centers require the zero test;
attached cells make local matching differ from whole-component square filling.
All labels are still obtained from the canonical Racket program.

Rejected: pure negative ordinary lessons, arbitrary noise-heavy scenes,
randomly corrupting positives without a construction invariant, and a solver
or answer cache inside the generator. Pure negative diagnostic textures remain
available for testing `self_check`, not ordinary training.

The tiny decisive witness is in `QUESTION_ANSWER.md`. Actual emitted examples
and their Racket/rival outputs are in
`checks/probe_final_v2/counterexamples.json`. All four first witnesses use
seed 0, sample index 2, difficulty easy.

## R1 — curriculum scheduling versus random mixtures

Choice: sample_index modulo 4 selects clean, clean, contrast, attached. Two
clean examples preserve the visual task; the other profiles guarantee at least
one refutation in any contiguous three-example unoverridden window. Slot
number is not part of the visible grid. Colors and geometry are still keyed
by seed/index. Every lesson label is computed independently from the input.

Rejected: independent 10% adversarial sampling, which can leave a complete
three-demo lesson ambiguous; putting all contrasts only in the hard band;
claiming that a single finite rival check proves universal identifiability.
Measured result: 0 survivors for each of four rivals in 1,500 overlapping
windows versus 1,500 survivors each before. This guarantee is for the normal
schedule, not arbitrary overrides that remove all decoys, shuffled examples,
or every possible sampling policy.

## R1 — preserve scale without pretending uniqueness improved everywhere

Choice: retain clean 7x9, 9x9 and 9x10 two/three-ring scenes. Extend other
profiles to larger legal grids and up to six positive rings, subject to capacity.
This gives both familiar demonstrations and harder predicate counterexamples.
Do not make every draw a large motif gallery: canonical-profile support matters.

Cost: clean slots share inputs across difficulty bands. Global unique inputs
fall from 2,036 to 1,586 in the matched 2,400-draw probes even though easy-band
uniqueness improves strongly. No held-out task accuracy improvement is measured.
Content-based deduplication across bands and training/evaluation partitions is
required before downstream use. Fixed small motifs are still a restricted
grammar; arbitrary adjacent layouts are tested as operator stress cases only.

## R2 — geometry and exact overrides

Choice: reserve 4x4 cells per motif with a blank-cell gap, random slack gaps and
D4 transforms. The protruding attached-ring cell fits the same reservation as
all other motifs. Separation prevents accidental joins and extra targets;
postconstruction observation checks the exact realized counts.

Capacity is floor((h+1)/5) * floor((w+1)/5). Pinned dimensions/counts are never
silently clipped. Defaults may be conditioned before they are recorded. An
impossible combination raises a named `IncompatibleOverrides` ValueError.
Rejected: retry-until-lucky placement, silently dropping rings, widening an
explicit requested canvas, or accepting every failed pair as a legacy exception.
The declared bounds 5..18, counts 1..6/0..6 describe an ordinary-domain
contract with possible structured joint incompatibilities, not a Cartesian
promise that every combination is geometrically realizable.

## R2 — remove fake knobs, preserve meaningful ones

Choice: keep height, width, ring count, decoy count, actual palette family and
texture. Remove `palette_size`, `n_distinct_colors`, `position_bias`, `density`:
the baseline never implemented them, and leaving silent names is worse than a
loud compatibility break. Version is bumped to 2.0.0. Unknown keys and
non-integer integer controls are rejected. Palette is not an exact distinct
color count; available slots and same-color repeats still matter.

Diagnostic texture names remain accepted explicitly but are not members of
`AXES.texture.valid`. They honor dimensions and reject positive motif-count
requests. Their fixed diagnostic colors are not controlled by `palette_kind`;
this branch is outside the ordinary palette contract and remains a documented
limitation, not an advertised production augmentation interface.

## R3 — keep one selected program, preserve archival evidence

Choice: copy the canonical selected program text into the bound base JSON's
active `racket_target.target_code`. Do not alter `program_solution` in the
canonical ledger, the bank's archival `raw_code`, or approval fields. Before
execution parity already passed, so this fixes authority identity, not a
proven semantic mismatch. The old target text is retained in
`checks/authority_sync_change.json`.

Rejected: deleting the long archival source, adding a second label-producing
Python authority, broadly rewriting canonical rows, or disabling source checks.

## Regression that changed the implementation

First patch's strict validator assumed foreground components could ignore
color. An official example contains different-colored rings that touch.
The failing 1/59 test and first-patch source are retained. Same-color components
now implement strict canonical inspection and the bounding-box rival; emitted
motif counts still use occupancy components because construction separates
those motifs. `observe_overrides` is explicitly not an arbitrary-image parser.

## Tooling, evidence and stopping decision

Build reusable local probes rather than prose-only findings:
`probe_distribution.py`, `audit_assigned.py`, and `run_portable_tests.py`.
Use `prepare_runtime` for the project's actual portable layout; save actual
runtime directories where tools expose them. Retain initial import failures
and code snapshots rather than overwriting them with successful reruns.

The two audit sources remain untouched. A1 has scoped clean evidence; A2/A3
are owner follow-ups, not patches sneaked into a separate assignment. The
shared fixture failure remains open as F1. Work stops with a source-bound,
all-green main battery, reproducible finite-rival evidence, required audits,
and a completed exposed-but-reference-closed solve; it does not claim universal
semantic coverage, improved model accuracy, or a globally green repository.
