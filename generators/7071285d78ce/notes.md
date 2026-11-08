# Current decisions: 7071285d78ce

## Current native parametric build

Implemented `selection=all|largest|smallest` in the separate task-local native
family. The alternatives render the exact canonical local transpose, then
recompute same-color four-connected components and retain all ties for the
selected occupied-area extremum. Real transformed mergers change component
rankings; selection before transpose is the tested causal counterfactual.

Teaching repair, focused tests, reviewer native qualification, causal replay,
saved public-preview verification and negative projection probes are complete.
The domain, source-bound evidence and finite limits are recorded in the native-extension
section below and `workspace/parametric/README.md`. Production and its inherited
source approval remain unchanged. Separate owner acceptance is still required.

The current review index has no active audits; the recorded Catalog status is
`audit_unresolved=false`, audit count 0 and pending-triage count 0. Historical
A7071-1 hold narratives are superseded by that current index. The counterexamples
remain preserved; this build neither newly resolves an audit nor admits training
data.

## Accepted fixed generator

Version 3.0.0 preserves the selected Racket authority (`9eb76f1bb8b7`). The rule
transposes each same-color, four-connected object about its own bounding-box
top-left and paints all results onto a blank grid of the original dimensions.
Python transforms in this generator are diagnostic competitors, not label code.

## Exact generation contract

Dimensions are independently exact in `8..14`, in every difficulty band. There
are exactly `2..4` separated objects with distinct foreground colors. `n_blobs`
is the count axis; `palette_size` and `n_distinct_colors` are exact compatibility
aliases. Conflicting explicit aliases raise a structured `ValueError` with
`incompatible_axes`. The old advertised distinct-color-count range `1..9` was unsupported by
the multi-object domain; it is now honestly `2..4`. Aliases are not additional
independent variation axes.

`palette_kind` (alias `texture`) selects default, warm, cool, or varied palettes.
Default means colors `1..n`; warm draws from `{2,4,6,7,9}`; cool from `{1,3,5,8}`;
varied mixes both families and excludes the exact default palette. Assignment
of the selected colors to objects is randomized. Legacy `density=sparse` and
`position_bias=spaced_nonsquare_blobs` are descriptive controls with one supported
value. The latter historical name does not forbid a nonidentity square bbox.
Negative textures remain callable fixtures, outside the valid production enum,
and `self_check` rejects them.

Shapes come from a deterministic enumeration of connected oriented polyominoes
of three through five cells, excluding rectangles and transpose identities.
This replaces the biased directional growth path. Source objects retain a
one-cell orthogonal separation. Transposed destination cells fit in bounds and
do not collide with other destinations. Source-to-destination overlap is lawful
and retained: forbidding it would contradict the blank-output Racket semantics.
Twelve random layout attempts are followed by a constructive corner fallback;
the fallback preserves exact controls and the lesson witnesses even at `8x8`
with four objects. It never silently returns an incomplete arrangement.

## Production lessons and shortcut coverage

The supported lesson is three demonstrations plus one query from four
consecutive accepted draws at one seed and band. The period-two schedule
alternates a canonical core with a broad witness profile. Its starting phase
is keyed independently of the sample index, avoiding the `seed == index`
collapse found in an earlier candidate.

The core uses two four-cell objects with `3x2` bboxes, including a fully
D4-asymmetric object, and favors the canonical canvas profiles. Each broad draw
contains both an asymmetric five-cell `2x4` object and a three-cell object.
Thus every four-draw window has two broad witnesses: holding out any one pair
still leaves demonstrations of both the size-three and width-four cases.
Extra broad objects vary across eligible shapes; explicit count/dimension
controls take precedence over canonical profile defaults.

Sixteen distinct diagnostic competitors cover identity, global transpose, six
wrong local D4 transforms, max/min-color selection, and six canonical-fitting
conditional shortcuts. The latter include ignoring three-cell objects and
restricting transpose to maximum extent three. An independent review reproduced
both missing-witness defects in the preceding candidate using actual Racket
labels; tests now retain those examples. A first successful census under a
smaller rival set was insufficient: rescoring its 300 lessons with the final
rivals found 39 production ambiguities and 179 ambiguous query rotations.

Final source `7d2106811736e477bb7cd903a72a1f1faed6abe8ae4d306e64a39415f3279e8d`
passed the twelve-stage battery, 16,470 exact-control draws, and a Racket-labelled
300-lesson / 1,200-rotation census against the final rival declarations. A
separate seed-zero enumeration covered both schedule starts across all three
bands: six overlapping lessons, 24 rotations, eight unique inputs, no ambiguity.
These are finite, declared-rival observations, not universal identifiability or
measured training gains. Exact settings, final test/replay counts and source-bound
receipts are in this review return's `RESULTS.json` and `checks/`.

## Retained findings and follow-up

Retained audit `A7071-1`, return `review-0e44dbe6aee8e6a8:v0001`, applies to source
`6940b446988027b5ca277abb707643959dfe35c593ee59ca87f957c006a4ccc9`.
Its exact seed-zero ignored-color-count and unsupported-boundary failures were
reproduced and repaired here; the original seven assets remain unchanged under
`counterexamples/review-0e44dbe6aee8e6a8-v0001/`. Current reproductions and
regressions are under `counterexamples/current_review/` and `tests/`.
The historical repair asked the maintainer to triage A7071-1. The current
`evidence/review_index.json` instead has an empty `audits` list and an approval
decision for source `7d210681...` and rule `9eb76f1bb8b7`. Earlier statements
that the current index still says `needs_triage` are stale. This records the
existing review state; the present parametric work does not newly resolve an
audit or alter that index.

The baseline seed-31 destination collision lost two color-2 cells under the
actual Racket rule; seed 26 supplies a lawful source/destination-overlap control.
`workspace/check_color_conservation.py` validates cached `arcpuzzles-apply-v1`
receipts under an explicit per-color conservation obligation. This inexpensive
opt-in tool does not assume conservation for unrelated ARC tasks. It validates
receipt structure and hashes and preserves the actual mismatch report.

Next useful work is broader independent rival search and eventual model-based
evaluation. Neither private-query correctness nor training-data admission is
asserted by these checks. Imported associated notes retain their original
evidence and timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `7d2106811736e477bb7cd903a72a1f1faed6abe8ae4d306e64a39415f3279e8d`.

# Decisions for 7071285d78ce

Assignment: `review-9263657a21a06d0b`. Final generator version: `3.0.0`.
Final SHA-256: `7d2106811736e477bb7cd903a72a1f1faed6abe8ae4d306e64a39415f3279e8d`.
The Racket authority and canonical data are unchanged.

## D1 — Exact controls describe the domain

Retained audit A7071-1 was reproduced on baseline source `6940b446...`: seed
0/index 0 ignored `n_distinct_colors=2`, while height 8 and count 4 were rejected
despite being declared valid. Dimensions `8..14` and counts `2..4` are now exact
in every difficulty band. Count aliases and palette aliases are consumed,
validated, and required to agree. The old advertised distinct-color-count range `1..9` was
narrowed to the supported multi-object domain `2..4`.

Treating aliases as independent axes creates impossible combinations and
misleading variation claims. They remain exact compatibility controls in
`AXIS_ALIASES` and metadata, with focused regression coverage. The single-valued
density and legacy position controls are explicitly diagnostic. Degenerate
textures remain negative fixtures, excluded from the production enum and
rejected by `self_check`. Explicit overrides take precedence over defaults.

Evidence: task-local `counterexamples/current_review/retained-audit-reproduction.json`,
`finite-probe.json`, `tests/test_transpose_regressions.py`, and
`checks/final-battery/checks/7071285d78ce_after_override_results.json`.
The final override census accepted 16,470 draws: 183 cases, 30 seeds per case,
three bands, zero findings and zero warnings. Alias tests supplement that
census; aliases are not counted as additional independent variation.

## D2 — Preserve objects under the actual label semantics

The Racket rule paints a blank output. Source/destination intersections are
lawful; destination/destination intersections overwrite cells. Baseline seed
31 lost two color-2 cells under actual Racket execution. Baseline seed 26
preserved all eight foreground cells despite lawful source/destination overlap.
Placement and validation now exclude destructive destination collisions while
retaining source clearance, bounds checks, and the lawful overlap control.

The shape pool enumerates eligible oriented connected three-to-five-cell
polyominoes, replacing a directionally biased random growth path. It includes
all canonical normalized shapes. Twelve random placement attempts are followed
by a constructive corner arrangement. A width-four witness has a reserved
`4x4` region; remaining regions are `3x3`, with at least one separating cell on
an `8x8` canvas. This fallback preserves exact controls and required witnesses
without dropping objects or claiming an incomplete arrangement is complete.

Evidence: task-local `counterexamples/current_review/racket-labels.json`,
the retained overlap regressions, and the independent 64-grid boundary check
in `checks/code-review-boundary.json`: seeds 0..31, indices 0 and 1, minimum
`8x8`, count four, all exact count and palette spellings supplied.

## D3 — Supply counterexamples in every supported lesson

The intended lesson has three demonstrations and one query from four
consecutive accepted draws at one seed and difficulty. Production holds out
the fourth pair. Rotation checks hold out each pair once and preserve the
remaining demonstration order. This does not certify every permutation of
demonstrations or arbitrary subsets of unrelated draws.

A period-two schedule alternates canonical and broad profiles. Its seed phase
is keyed independently of the index. The rejected `(seed + sample_index) % 2`
implementation collapsed on the common diagonal `seed == sample_index`; the
final 32-call diagonal probe saw both profiles: 14 broad and 18 core.

The core uses two four-cell `3x2` objects, including a fully D4-asymmetric shape,
and favors the canonical `10x10`, `9x11`, and `8x12` canvases. Every broad draw
contains a three-cell object and an asymmetric five-cell `2x4` object. Two
broad draws in each four-pair window mean any single-query holdout retains
both witnesses in its demonstrations. The fallback preserves these shapes;
optional extra broad objects vary by difficulty. Exact count and dimension
overrides take precedence over canonical profile defaults.

The final semantic sample had 296/600 canonical-profile hits, 49.33% against a
declared 45% floor: easy 111/200, medium 92/200, hard 93/200. All five canonical
inputs were accepted. This deliberately combines canonical support with broader
examples; it does not reproduce the empirical ARC distribution exactly.

## D4 — A green report is only as broad as its tested rivals

Independent review found two genuine gaps in the preceding source despite its
green 14-rival checks: ignoring three-cell objects and ignoring objects whose
maximum bbox extent exceeds three could fit all demonstrations and fail the
query. Actual Racket-labelled witnesses are in `checks/code-review-shortcut.json`
and `checks/code-review-extent-shortcut.json`. Two independent tests failed
before the repair and passed afterward.

Final declarations contain 16 distinct competitors: identity, global transpose,
six wrong local D4 transforms, max/min-color-only transforms, and six conditional
shortcuts that fit all five usable canonical pairs. Some names appear under
multiple hook namespaces in reports; those are not extra distinct hypotheses.
The tools enumerate the actual declarations rather than a copied rival list.

Rescoring the earlier 300 actual-label lessons with the final rivals found 39
ambiguous production lessons and 179 ambiguous rotations out of 1,200. These
failures remain retained. The final generator had zero ambiguous lessons out
of 300 and zero ambiguous rotations out of 1,200 against those same final
rivals. It produced 1,200 unique inputs. The census uses its recorded SHA-256
seed recipe for each easy/medium/hard band and index 0..99; every exact seed
and instance is retained.

The fixed-seed schedule census enumerated both starts in period two across all
three bands: six lessons, 24 rotations, eight unique inputs because windows
overlap. It found no ambiguity. The general census's generic residue field
uses period six; the explicit schedule census is the evidence for the actual
period-two starts. This is finite declared-rival coverage, not universal
identifiability. Further independent hypotheses can reveal new gaps.

Evidence: `checks/prior-lessons-rescored.json.gz`,
`checks/final-lesson-census.json`, `checks/schedule-census.json`,
`checks/code-review.json`, and task-local `tests/test_curriculum_contract.py`.

## D5 — Build the reusable gate within the allowed task scope

`workspace/check_color_conservation.py` checks per-foreground-color mass in
existing `arcpuzzles-apply-v1` receipts. It verifies schema, required identity
agreement, grids and hashes before comparing counts. It does not execute or
replace Racket and does not impose conservation on other ARC tasks. Seventeen
tests cover the real failure, lawful overlap, shape/background changes,
malformed evidence, hash errors, color substitutions, and output-overwrite
refusal. F1 proposes separate shared integration; frozen shared files are intact.

## Scope of the accepted 3.0.0 repair

That repair changed the selected generator's implementation, notes, tests,
workspace tool and counterexamples. Its two audit-only targets were unchanged;
their four reproduced findings belonged to that earlier assignment's `AUDIT.md`.
The current review index, rather than the old pending-triage narrative, records
the inherited approval state. The earlier repair claimed no private query
scores, model-training improvement or training admission.

## Native parametric extension: transpose, then select

`workspace/parametric/` adds the separate native parameter
`selection=all|largest|smallest`. `all` returns the exact selected canonical
Racket source. The alternatives first render the same blank-canvas local
transpose, then recompute same-color four-connected components and retain all
ties for largest or smallest occupied-cell count. Component identity, not
global color totals or bbox area, defines the selection unit. Separated
same-color source pieces genuinely merge after transpose; the first teaching
scene changes source areas `2,3,4,4` to intermediate areas `5,4,4`. Selecting
before the transform therefore changes either alternative's output.

The prototype validator admits rectangular `8..30` grids, `2..24` components,
repeated foreground colors, and connected shapes including square bboxes,
rectangles, identities, lines and singletons. All source components have
orthogonal clearance, even across colors. Transformed cells must fit and
destination sets must be disjoint; lawful source/destination intersections
remain supported. These are explicit extensions of the unchanged production
generator. The sampler uses bounded constructive profiles, not every grid
admitted by the validator. Its `30×30` query contains 24 source components and
112 occupied cells distributed across eight merger tiles and all four borders.

The native adapter accepts exact integer seeds `0..2**63-1`, independently
requested `3..6` demonstrations and `1..4` queries, and exactly one supported
selection key. Booleans and floats are rejected. Omitted settings use seed
modulo three. Full banks are built before slicing with independent local RNG
streams, giving matched inputs across settings and stable requested prefixes.

### Teaching correction and finite evidence

Independent review of seed 0 under `smallest` found that two shortcuts fit all
three original demonstrations: transpose only nonsquare-bbox objects, or only
source objects of at most five cells. Both disagreed on query indices 0, 1 and
3. Revised demonstration index 1 visibly selects nonidentity six-cell
square-bbox shapes and refutes both. All four query inputs and labels and the
intended program are unchanged. The original source and failing lesson remain
in `checks/7071285d78ce/self-review-nonsquare-v1/`; the protected 29-execution
repair replay is `checks/7071285d78ce/self-review-repair-proof.json`.

The final focused suite records 111 passing tests: 28 family, 66 sampler and
17 adapter tests (`checks/7071285d78ce/native-tests-final.xml`). The expanded
`audit-r2/audit.json` checks all settings at seeds 0 and 17 with three demos and
four queries: 168 comparisons, 152 demonstration refutations, 16 finite-consistent
comparisons with matching tested queries, zero query conflicts or execution
errors, and 347 protected Racket executions. It also checks five canonical
pairs and unchanged source bindings. `boundaries.json` records 30 protected
labels at the maximum seed with six demos and four queries under each setting.
These evidence paths are relative to `WORK/checks/7071285d78ce/` unless their
full `checks/` prefix is given. The initial audit is superseded, not erased.

The rival set distinguishes same-color eight-connectivity from color-blind
four-connectivity; the latter uses binarization plus `objects`, because the
prelude's `objects-multicolor` actually uses eight neighbors. Finite-consistent
rivals are not described as disproved, and failed execution is never teaching
evidence. The observations establish only the recorded finite coverage.

Native reviewer qualification passed six of six jobs with 78 protected Racket
evaluations in `checks/7071285d78ce/qualification/`. Its qualification SHA-256 is
`113120f70ac2b17b208193bf29ed4ade4e95b6cc676eaf94e61cd7b3894b85f4`.
The source-bound `causal/witness.json` and `causal/replay.json` contain two
wrong-order cases: largest and smallest selection change 13 and 10 output
cells, respectively. Construction and independent replay each used four
protected evaluations. The intermediate descriptions remain authored causal
arguments, not universal proofs. The sequential public preview under `preview/`
exported and verified 24 one-query views. `public-rejections.json` confirms
rejection of a leaked query answer, an orphan public file and a missing public
view, with the original bundle unchanged. Projection checks do not replay
Racket. These paths are under `checks/7071285d78ce/`.
Separate owner acceptance of the exact integrated source is still pending;
training admission is false. Reproduction commands and the complete domain
are in the adjacent parametric README.
