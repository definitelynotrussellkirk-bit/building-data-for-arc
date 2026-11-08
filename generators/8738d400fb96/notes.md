# Current decisions: 8738d400fb96

## Rule and authority

Version 2.0.0 retains canonical rule `fc4e32aa0363`: select the uniquely largest
same-color four-connected color-3 component, translate by marker1 minus marker2,
and paint color8 on a same-size zero canvas. Paint clips at the boundary; a
completely empty output is lawful. Markers may touch the green component.

Canonical program SHA256 is
`46742b981c00393650e16214ec1f0f47c142090a9767003617126ccaecda8e9e`.
Only the selected active target's two extra comments were removed to match this
exact canonical text. The canonical ledger, labels and executable semantics did
not change. Earlier input-choice rationale was unknown: notes were boilerplate.

## Reversed restrictions and implemented choices

The original generator moved only down/right, excluded clipping, omitted foreign
colors and size6 shapes, ignored `blob_size`, accepted missing-marker fixtures,
and advertised inactive palette/texture controls. These restrictions excluded
canonical behavior: three signed quadrants, partial clipping, an empty output,
foreign colors, and a six-cell main shape. The initial battery had five failed,
two advisory and five green stages.

The new exact integer controls are grid_h8..16, grid_w10..18, and blob_size3..9.
None means omission; booleans, wrong types, obsolete/unknown keys and out-of-range
values raise errors. Every advertised joint combination is constructive. Shape
mass and dimensions are recovered from returned pixels. Difficulty changes
weights without changing the legal override domain. Canonical-size/palette
profiles are mixed with broader canvases; no saved canonical grid is replayed.

Default shapes are connected polyominoes in a4x5 bounding box. Marker deltas range
from -4..4 rows and -5..5 columns, excluding zero; all eight direction classes
occur. Each input uses one foreign color chosen from4..9. Some foreign components
are larger than the main shape, and some translated foreign cells remain visible.
Smaller green components, diagonal contacts, placement, shape and noise vary.
The validator admits a broader domain, including two-cell main shapes; it rejects
largest-green ties, missing/duplicate markers, malformed grids and noninteger
colors. It does not mistake clipping or marker contact for invalidity.

## Teaching contract

Eight demonstrations and one query use four repeating semantic positions:
(0) a full signed selector contrast; (1) a varied full example; (2) partial
clipping; (3) complete clipping. Repeated contrasts distinguish selecting all,
first, last, eight-connected or nonsingleton green components, the largest object
without regard to color, moving every nonmarker cell, fixed3/4 steps, absolute or
swapped vectors, reverse vectors, wrapping, avoiding clipping and omitting
recoloring. Fourteen named rivals are executable diagnostics; Racket supplies
all reference labels.

Every nine consecutive accepted samples retain repeated witnesses, so a single
holdout can preserve the required examples. This is verified against the actual
production sampler, including its accepted-index metadata: 300 lessons and2,700
query rotations had no ambiguity against the named rivals; all four schedule
starts at seed0 across three bands added12 lessons/108 rotations without
ambiguity. These finite results do not prove unique induction or shorter-lesson
support. Arbitrary new overrides/populations still need their own assembly check.

The ordered full/full/partial/empty pattern exposes a retention-class cue. An
order-aware consumer can infer some empty queries from position. This is a
known curriculum limitation, not a demonstrated wrong query against the declared
rivals. Downstream pair shuffling is a separate choice supported by the measured
holdout evidence; it was not silently added to the shared sampler.

## Verification and retained failures

Final generator SHA256:
`3aab56e6138452da15192da2294ef0b81b1f053014b433e84a52b1c32db836b0`.
The final required battery is12/12 green, strict domain600/600, and canonical
acceptance5/5. The portable selected task suite passes100 tests. Its independent
oracle reproduces the canonical labels, covers2,268 joint axis/phase combinations,
and retains literal Racket-verified border and component counterexamples.
Independent review added224 boundary draws and36 public Racket comparisons,
without a generator defect.

A first repair still allowed axis vectors(0,-4)and(-3,0) in its designated
fixed-step separator; seeds148/182 demonstrate the problem. The repaired filter
and regression tests cover these cases. An intermediate battery also caught a
missing public schedule_profile hook and an identifier-only lint warning; those
failures remain retained. See counterexamples/ and workspace/PROGRESS.md.

The source-bound output-profile tool in workspace/ compares canonical
full/partial/empty support with existing reference-labelled evidence. Independent
review found and fixed two receipt-consistency defects: incomplete or substituted
canonical mappings and contradictory source fields. The tool now reads the actual
canonical ledger, verifies the complete pair mapping and cross-checks rule/ledger
bindings. It remains a finite coverage diagnostic, not a proof of label correctness,
cryptographic receipt authenticity, approval or training admission.

Owner checks separately exercised this diagnostic over the retained baseline and
repaired reference labels: the baseline lacks partial/empty classes in each band;
the repaired census has 450 full, 225 partial and 225 empty pairs per band.
No labels were recomputed. The report writer now exclusively creates a new file;
existing inputs, ledgers, reports and symlinks are preserved. Five CLI regressions
failed before that repair; all 31 focused tool/integrity tests pass afterward.
The generator's larger battery and semantic counts above remain reviewer-reported.
## Current reviewer considerations

Source SHA-256: `3aab56e6138452da15192da2294ef0b81b1f053014b433e84a52b1c32db836b0`.

# Decisions for review-e9de73aae23eac88

The new random draw selected 8738d400fb96. The original uploaded ZIP was extracted
fresh; the previous round's source, draw, receipts and return were not reused as
measurements of this source. The baseline has no useful task notes, tests or
pending repair index; original rationale for its restrictions is unknown.

## Input and authority choices

| Choice | Previous behavior | Implemented choice and evidence | Alternative / limit |
|---|---|---|---|
| Displacement | Positive row and column only | Signed vectors, including axis-aligned moves; all eight classes observed in independent tests and boundary probes | A zero vector is impossible with distinct color-1 and color-2 marker cells; it is not advertised |
| Clipping | Moved shape must fit | Full, partial and empty results are ordinary profiles; canonical train pair 3 is empty and test pair 0 is partly clipped | Rejecting blank output would exclude an actual canonical label |
| Shape selection | One green object only | Smaller green components, including diagonal contact, distinguish selection of the largest four-connected component | Largest-size ties are excluded from the generated/validated teaching domain |
| Nuisances | None | One connected foreign-color component, sometimes larger than the main and visibly translated by wrong rivals | Exactly one foreign color/component remains a default restriction |
| Semantic colors | Inactive palette controls | Marker colors 1/2, shape color 3 and output color 8 stay fixed; nuisance color varies over 4..9 | Arbitrary palette permutations would change the authoritative rule |
| Shapes | Random mass 3..5; ignored `blob_size` | Exact mass 3..9; connected polyominoes within a 4×5 bounding box | Validator admits two-cell shapes; larger/longer shapes are not promised generated support |
| Dimensions | Advertised bounds disagreed with difficulty bounds | Exact height 8..16 and width 10..18 in every band; 2,268 joint axis/phase combinations exercised | The bounds are constructive training choices, not the whole Racket domain |
| Overrides | Ignored keys and pseudo-degenerates | Only three exact integer axes; `None` means omission; invalid/obsolete controls raise | Retaining inactive API labels would misrepresent the actual distribution |
| Rule text | Selected target had two extra comments | Delete only those comments to match exact canonical source | No Racket semantics, canonical labels, raw_code or ledger changed |
| Canonical support | Palette size 4 and no clipped outputs | Mixed canonical-size/palette anchors and broader draws; exact profile hits: 11/20 easy, 18/20 medium, 15/20 hard | Matching marginal profiles alone cannot establish teaching quality |

The marker-placement fallback no longer returns incomplete scenes. Layout search
returns a complete lawful scene or raises explicitly. All random decisions use
keyed generator context draws; no generated labels are supplied by Python.
`self_check` examines actual pixels and does not accept metadata as a bypass.

## Lesson assembly and alternatives

We chose eight demonstrations plus one query and four semantic positions:
full signed contrast, varied full, partial clipping, complete clipping. The
full signed contrast separates all seven object-selection rivals plus absolute,
fixed 3/4-step and swapped displacement rules. Other roles expose clipping and preserve
simple full examples. Each role repeats within the nine-pair materialized window;
one holdout therefore leaves useful demonstrations. The tentative six-demo/three-
position alternative would either remove simple full cases or correlate full
visibility with a narrower vector class; the extra two demos were a deliberate
cost for a clearer contract.

The production census of 100 lessons per band used the actual shared sampler, not
a custom replacement, with accepted pair indices recorded. All 300 lessons and
2,700 query rotations had no ambiguity against 14 distinct named rivals, with
namespaces retained.
A separate seed-0 enumeration covered all four declared starting residues in all
three bands: 12 lessons/108 rotations, also with no ambiguity. This is not proof of unique
induction or every random start/seed, and rotations are not independent draws.
Shorter lessons and arbitrary changed override populations are unverified.

The order exposes a repeating retention class. An order-aware consumer can infer
some blank queries without consulting their vectors. We preserve that limitation
explicitly; the source/assembly contract was not silently changed after review.
Pair shuffling can remove the position cue while keeping the demonstrated role
multiset, but is a separate downstream choice. The minimum nonmarker color also
identifies green within this fixed-color domain; it is answer-equivalent here,
not evidence that a legal color-role swap was tested.

## Failures that changed the implementation

The original battery had 5 failed, 2 advisory and 5 green stages. Independent tests
initially had 47 failures, including ignored overrides and missing-marker acceptance.
The first repaired source passed 68 focused tests, but a targeted 1,000-seed probe
found 24 axis-vector cases where the signed fixed 3/4-step rival survived the
designated contrast.
Seeds 148 and 182 remain in counterexamples/ and failed regression tests before the
filter fix. The next battery caught a missing `schedule_profile` hook and a local
identifier lint warning; both were fixed, and that complete failed run remains.

Independent final review found two Important defects in the new coverage tool:
canonical mappings could omit or substitute clipping cases, and contradictory
rule/ledger metadata could pass. Eight targeted tests failed first. The final
tool reads the actual canonical ledger, checks every canonical identity and pair,
and verifies census program, declared rule and ledger bindings. Nine integrity
tests and all 100 portable task tests then passed. No original failure was rewritten
as a successful run, and no deliberately wrong solve was presented as an accident.

## Scope, acceptance and storage of evidence

The final source is `3aab56e6138452da15192da2294ef0b81b1f053014b433e84a52b1c32db836b0`.
An independent review covered 224 new boundary draws and 36 Racket comparisons without
finding a generator defect. Source/rule/test hashes, exact commands, finite scopes
and both solve exposure declarations are retained. The pre-repair blind task is
separate from the exposed post-repair solve. Both private query scores are unknown.

The return contains a task repair and evidence; it does not perform model training,
certify empirical Qwen gains or admit trajectories to a training set. Large JSON
receipts are losslessly compressed with restoration metadata to meet the official
return budget, rather than discarding failures or weakening the packager.

The first return-building attempts were rejected by the unchanged official builder:
two exceeded the 25 MiB expanded limit when raw census copies were present, and
one used an unsupported intermediate completion-state label. The retained receipts
record those failures. A separate staging copy with byte-verified gzip evidence
and the documented `in_progress` state passed the official builder. Final replay
and final packaging use that same frozen source patch; no size limit or validator
was modified.

Final replay passed all 100 selected portable tests using the fresh extraction's
own Python environment and Racket runtime. Both patch-check and application
succeeded; all 16 changed paths and the 17-file generator home were byte-verified.
The initial assumption that the patch count equalled the full-home file count was
a bookkeeping error, corrected before application and retained in the receipt.
The final return state is `complete`, with routine acceptance and the documented
population limits.
