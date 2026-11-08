# Working notes: c5a80b7a3acc

## Authority and scope

Review `review-839c52ef87471169` replaces imported v2.3.0 with v3.0.0. The
canonical rule and every shared implementation/fixture remain unchanged.
`RULE_HASH=db99a498afde`; full canonical source SHA-256 is
`db99a498afdedcc650e775a4492ff2a9a7f605cafc4725ca0a9250dfd6062cf2`.
Canonical evidence contains two training pairs and one usable test pair. All
three have one red and one green component, shapes within 3x3 envelopes, and
8x14 or 9x15 inputs. Their incidental marker positions, relative placements,
and area order do not define the rule.

For the supported domain, normalize the two shapes separately, intersect if
any 7 exists, otherwise XOR, and tightly crop the selected cells in color 8.
The result may be empty, represented by `[[0]]`. Color 9 never selects an
operation. The Racket object routine selects the first row-major component of
each source color when several exist; generation and validation deliberately
require exactly one component of each color to avoid teaching that incidental
selection behavior. Tests use a separately written pixel oracle, while census
and semantic witness labels are obtained through the public Racket runner.

## Defects motivating the rewrite

The original marker could overwrite a source pixel: seed 799, sample 0,
`marker=1` removes a bridge at (10,7) and splits red into two components. Its
advertised dimension controls did not consistently accept their declared range.
Growing both shapes from the same common core and adding equal extras strongly
restricted source cardinalities and XOR parity; the canonical XOR has five
cells. Textures did not reliably implement their advertised meanings. The old
validator rejected lawful empty answers and a lawful no-marker texture. There
was no executable semantic teaching contract or pinned rule hash.

No associated design rationale or prior return for this selected task was
found in the supplied evidence. Claims about the author's intent would be
speculation. The retained review ZIP includes the original failing battery,
66 failing / 39 passing new regression tests, and the exact marker reproducer.

## Constructive shape and placement choices

Enumerate the 151 nonempty, normalized, 4-connected masks within a 3x3 envelope.
Choose ordered mask pairs with an exact intersection cardinality. The finite
catalogue provides termination and lawful connected sources without rejection
walks or truncation. Every canonical source envelope is covered; this is not a
claim to sample larger valid shapes. Difficulty changes pair weights and overlap
preferences without removing legal pair support.

All integer heights and widths in 8..16 are supported independently in every
band. A weighted canonical dimension anchor favors (8,14) and (9,15), with a
broad component retaining other sizes. Independent position lists are shuffled,
then the first noncolliding pair is selected. Witness-role row envelopes have
at least one blank row between them to distinguish independent normalization
from absolute-row alignment. Broad samples allow every noncolliding placement
within the grid. This method is not uniform over placements. Markers are drawn
only from the remaining zero cells; object geometry is never overwritten.

The 3x3 bound keeps pair-pool enumeration small and covers the observed task
scale. A larger random-walk envelope was rejected because it increases packing
and termination complexity without evidence that it is needed here. A single
shared core was rejected because it suppresses disjoint/unequal shapes and can
hide parity restrictions. Fixed red-left/green-right placement was rejected
because color, not physical order, identifies the operands.

## Exact controls and intentional restrictions

| Control | Meaning and supported values |
| --- | --- |
| `grid_h`, `grid_w` | Exact visible dimension, each integer 8..16. |
| `core_size` | Exact size of the independently normalized intersection, integer 0..6. This replaces the old latent growth-core meaning. |
| `marker` | Exact presence of at least one 7, integer 0 or 1. It does not specify the presence of 9. |
| `texture` | `mixed`, `and_mode`, `xor_mode`, `identical`, `disjoint`, or `no_marker`; a sampling policy rather than a unique observable class. |

`observe_overrides` measures dimensions, normalized overlap and presence of 7
directly from pixels. Unknown keys, invalid difficulty values, booleans passed
as integer controls, nulls, strings and out-of-range values raise `ValueError`.
Supported difficulties are `None`, `easy`, `medium`, and `hard`.

The only declared control conflicts are AND mode with marker 0, XOR/no-marker
mode with marker 1, disjoint texture with positive overlap, and identical
texture with zero overlap. These report structured incompatible axes. No-marker
means neither 7 nor 9. Identical/disjoint/no-marker are classified as lawful
degenerate textures; empty outputs are valid. Shape overlap 7..9 is outside the
advertised sampler range, although the validator accepts broader lawful inputs.

Explicit `texture`, `marker`, or `core_size` invokes the broad construction so
all legal requested combinations remain available. Dimension-only overrides
retain the teaching schedule. Consequently a caller that fixes one operation
must not assume the default lesson guarantee. Explicit `texture='mixed'` is
also an intentional request for the broad policy.

## Teaching contract and its proof

Six canonical-fitting rivals are declared: area-based operation selection,
top-left-only 7, top-row-only 7, selecting XOR by 9, absolute-row alignment,
and retaining the normalized origin instead of cropping. Seven additional
lesson competitors are always-AND, always-XOR, union, either operand, and either
directed difference. Declarations are executable and reusable probes enumerate
the live mappings rather than copying a list of rival names.

The default role is `(seed + sample_index) % 3`:

1. AND witness: nonempty intersection with a positive top or left minimum;
   red larger than green; intersection crop different from both XOR and
   green-minus-red crops; 7 below row zero and an irrelevant 9 present.
2. XOR witness: positive overlap, red smaller than green, odd XOR cardinality,
   and XOR crop different from intersection; 9 present and 7 absent.
3. Broad pair: either operation, all declared overlap values, varied area
   orders, marker palettes, geometry and placements.

Every AND witness refutes eleven competitors. Area order and marker placement
refute the four selector shortcuts and always-XOR; separated rows refute
absolute-row alignment; the leading margin refutes no-final-crop. Intersection
is a proper subset of each operand, so copies and union differ. The explicit
crop comparison refutes green-minus-red. Every XOR witness refutes always-AND;
its larger green operand supplies at least one green-exclusive cell, so XOR has
more cells than red-minus-green. Together these roles refute all thirteen.

Every six consecutive default samples contain two of each role. Removing one
query leaves at least one AND witness and one XOR witness among five demos.
The finite construction proof therefore supports all six cyclic query choices,
in addition to the sampled production census. It does not prove uniqueness
against arbitrary undeclared programs or apply to reordered, shorter, or
semantically forced lessons.

## Important failed iteration and repair

The initial v3.0.0 candidate passed 105 tests, the full battery, and a 300-lesson
census. Independent review still found ambiguous cyclic lessons at hard seed
259 and easy seed 4702 (samples 0..5): green-minus-red agreed on pairs 0,1,3,4,5
and disagreed on pair 2. All twelve labels were checked with public Racket
apply. Two genuine regression tests failed before the fix. The final AND-pool
predicate excludes the cropped green-minus-red collision; all 107 tests then
pass. Both iterations remain distinguished by complete source hashes in the
review evidence, rather than being silently treated as one passing version.

The final pool probe checks 2,190 distinct AND pairs and 5,562 XOR pairs using
diagnostic labels and one lawful representative placement per pair. It is a
bounded cross-check of the proof, not 7,752 additional Racket executions or an
enumeration of every placement. `workspace/check_witness_pools.py` is reusable.

## Validation and remaining sampling limits

The validator accepts rectangular ARC grids up to 30x30, palette 0/2/3/7/9,
and exactly one connected object of each source color. Strict canonical-like
validation uses this lawful domain; measured canonical-size/palette support is
reported separately rather than conflated with 100% strict validity.

The final source-bound census contains 100 production lessons per band, 1,800
unique input grids, and 1,800 cyclic query windows over those same grids. Every
declared competitor is refuted in every window. Broad samples show both unequal
area orders in each operation and band, so witness roles do not create a
universal area selector. Nevertheless modes and area order remain correlated;
empty XOR occurs only once in these 1,800 inputs and is directly available via
identical texture. Frequency is not a guarantee of per-lesson support for
every edge case. These limits are explicit rather than inferred away from
passing checks.

The permanent tests cover controls, canonical validation, marker preservation,
connectedness, lawful edge cases, parity/area variation and the two actual
teaching regressions. The lesson audit refuses stale/partial/error census
records, replays only inputs to recover actual sample indices, and preserves
public Racket outputs and failures. Both tools refuse output overwrite.
## Current reviewer considerations

Source SHA-256: `f0f0a91ec4699b91b0a6ca565f1591975103c463047cb3dc00c5253f8aa813a9`.

# Decisions — c5a80b7a3acc, review-839c52ef87471169

## D1 / R1 — Preserve geometry before placing markers

The baseline wrote a marker into an arbitrary bottom-row cell after painting
sources. The exact seed-799 bridge overwrite established an actual connectedness
failure. The repair samples marker cells from the visible zero set after both
objects are placed. Fixing one preferred marker position was rejected: any 7
anywhere is authoritative, while the canonical top-left location is incidental.
Markers may be outside row zero, 7 and 9 may coexist, and no-marker inputs are
lawful. The canonical Racket rule remains unchanged.

## D2 / R2 — Use finite connected masks instead of shared-core growth

The original common-core construction encouraged equal operand areas and even
XOR counts. It also obscured whether a requested core size survived growth.
The new catalogue contains all 151 normalized connected masks in 3x3. Pair
selection filters the actual normalized intersection cardinality before
placement. This makes overlap exact, bounds construction, permits unequal and
disjoint shapes, and supports odd XOR results like the canonical five-cell
example. Growth-and-retry with larger envelopes was rejected because it adds
packing and termination risks without evidence that larger shapes are needed.

The explicit limitation is meaningful: the generated envelope is at most 3x3,
and overlap controls cover 0..6 rather than every overlap allowed by the
validator. The shape catalogue is broader than the three canonical pairs but
is not the entire reference-lawful domain. Difficulty changes weights rather
than legal support. Cached pools are immutable tuples with bounded keys.

## D3 / R2 — Separate visible controls from sampling policies

Heights and widths are exact independent integers 8..16 in every band, with
(8,14) and (9,15) favored to maintain canonical size/palette support. Retaining
difficulty-dependent dimension rejection was rejected because it contradicts
the advertised axes. The final profile result is 23/60 exact matches; it is
reported separately from 600/600 strict validity.

`core_size` now means the visible normalized intersection count. That is an
intentional contract change from an internal growth seed, accompanied by a
major version bump. `marker` means presence of 7, not presence of 9 or a fixed
header location. `observe_overrides` computes those quantities from the grid.
Texture is a policy: different texture names can yield the same lawful pixels,
so the observer does not pretend to recover a unique texture label.

All six textures are implemented. Identical and disjoint refer to normalized
shape relations, not physical co-location. No-marker excludes both 7 and 9.
Only the four declared impossible combinations are rejected, with structured
axis evidence. Invalid types and unknown keys are rejected instead of silently
ignored. Exact controls select the broad path when any of texture/marker/core
is explicit; this avoids a teaching-role restriction making a lawful forced
combination unavailable. A forced single-mode lesson therefore does not claim
to teach both operations. Dimension-only controls preserve the schedule.

## D4 / R2 — Keep the label authority and accept lawful empty results

The three canonical examples and public Racket execution establish independent
normalization, any-7 precedence, ignored 9, AND/XOR selection, final tight crop,
and `[[0]]` for the empty set. There was no evidence justifying an authority
change. The old nonempty-only validator restricted this lawful behavior, so
validation now permits empty AND and identical-shape XOR. The generator module's
set computations construct witnesses and rivals; they do not replace the Racket
labeler. The test oracle is separately written from pixel sets.

Exactly one connected object per source color is enforced. Racket's first-object
selection on multiple components is deliberately excluded from the teaching
domain. Unknown colors or ragged grids are rejected. Validation permits larger
lawful shapes than sampling produces; that support distinction is documented.

## D5 / R3 — Teach two complementary witnesses within five demonstrations

Six plausible rivals fit every usable canonical pair. Arbitrary random witness
frequency does not ensure a particular lesson teaches them. The chosen period
three is AND witness / XOR witness / broad pair, with EXAMPLES_NEEDED=5. Six
consecutive pairs contain two of every role; any single query removal leaves
one of each witness among five demos. This fits the shared maximum of five
demonstrations and provides cheap coverage of every cyclic query choice.

AND witnesses reverse the canonical area correlation, place 7 below row zero
alongside an irrelevant 9, separate source rows, and require a nonempty cropped
intersection with a leading margin. XOR witnesses supply the complementary
operation with positive overlap and odd output size. Broad pairs counterbalance
area orders, marker palettes and placements. A fixed left/right arrangement,
always equal areas, mandatory nonempty outputs, and a larger schedule with
insufficient witnesses after query removal were rejected.

The final proof covers the actual thirteen lesson competitors. An AND witness
refutes eleven; an XOR witness refutes always-AND and red-minus-green, as well
as several others. Their union is all thirteen. This proof depends on the
stated default assembly, not arbitrary shuffling or truncation. Cyclic rotations
here are adversarial alternate query choices over production-materialized
pairs; they are not a claim that the shared sampler itself rotates queries.

## D6 / R3 — Preserve the failed passing-looking iteration

The initial v3.0.0 candidate passed the battery, 105 tests and 300 production
lessons. Independent review found that hard seed 259 and easy seed 4702 still
allowed green-minus-red to fit pairs 0,1,3,4,5 and fail query pair 2. The defect
was a cropped-shape collision, so label correctness did not prevent lesson
ambiguity. Supported public Racket apply checked all twelve retained grids.

The minimal final repair rejects an AND witness when its intersection crop
equals the green-exclusive crop. It leaves broad control support unchanged.
Two regression tests failed before the repair and pass afterward. The old
generator, exact lessons, labels, failures, census and solve remain retained;
full hashes distinguish the unshipped iterations. A bounded exhaustive role
probe now supplements sampling: 2,190 AND plus 5,562 XOR distinct pairs, using
diagnostic labels and representative placements. The construction argument
handles placement-dependent claims. No universal program-identifiability claim
is made from either the census or this finite proof.

## D7 — Build tools for the next reviewer

`workspace/audit_lessons.py` consumes a completed public census, binds generator
and authority hashes, checks every live canonical-shortcut declaration on all
usable canonical pairs, recovers actual accepted indices by input replay,
and tests six query positions. It reports refuted rivals, rivals surviving all
pairs, ambiguous queries and scoring errors separately. Exact generated
counterexamples and distribution statistics are retained. It refuses stale,
partial or error-bearing census input and will not overwrite output.

`workspace/check_witness_pools.py` records live declaration names, source hashes,
validation results and guaranteed refutation intersections for all distinct
witness shape pairs. It explicitly labels its oracle diagnostic. Keeping this
as a small runnable tool was preferable to reporting an unreproducible proof
search. Both tools use the current selected source rather than embedded copies.

## D8 / R4 — Preserve isolation while making portable tests work

The default interpreter's pytest lived in user site, which public child
execution intentionally disables. The shared fixture failure was fixed by
provisioning already installed third-party distributions in an isolated local
environment. Source, fixture and isolation policy stayed unchanged. Once pytest
actually ran, it exposed a local sibling-import assumption in the new teaching
test. That import now resolves the exact adjacent test file by `__file__` under
both normal and portable import modes. The final staged run passes all 107
tests. Both causes and the original failure evidence remain available.

## D9 — Keep audit findings within their measured scope

Audit A1 is a restriction on ordinary bars: its rival is equivalent throughout
that ordinary domain and differs on an explicitly generated singleton texture.
A638-1 is a reproduced exact-control defect. A638-2 is a count restriction whose
distinguishing input passes validation but lies outside the declared generator
invariant. Neither domain limitation is relabeled as an observed ambiguous
ordinary query or an incorrect Racket label. Both audit targets remain unchanged.

## D10 — Preserve solve exposure and handoff provenance

The required blind solve was completed first and honestly declares no earlier
exposure. The final task was solved from visible examples in a clean agent
context, with packet-level exposure conservatively yes because the coordinator
had audited the rule. Queries were executed but their scores stay unknown.
Earlier-source and carryover episodes are archived, including failed finish
operations; repeated managed execution of the same candidate is not counted
as additional independent solver discovery. The final finish snapshot is
created by the supported tool and bound to the final generator source.

The exact delta was replayed against a new extraction of the original packet:
apply check and application succeeded, the source hash matches, and all 107
selected tests pass in an independently provisioned portable runtime.
Shared optional feedback remains a separate patch,
outside the task source delta, and no approval/training status is changed.

## 2026-10-24 native parametric review

- Preserved `generator.py` byte-for-byte at SHA-256 `f0f0a91ec4699b91b0a6ca565f1591975103c463047cb3dc00c5253f8aa813a9` and preserved the canonical Racket program at SHA-256 `db99a498afdedcc650e775a4492ff2a9a7f605cafc4725ca0a9250dfd6062cf2`.
- Added a task-local native family with `result_policy=direct|largest_component`. `direct` is the exact canonical program. `largest_component` first performs the canonical marker-selected normalized intersection/XOR, then selects and crops the largest four-connected component of that Stage-A result, with a row-major top-left tie break.
- The adapter supports 2–6 demonstrations and 1–4 queries, always retains four deterministic novel queries, keeps inputs matched across settings, includes a substantive 30×30 case, and writes one-query public projections without answers or future-query-count hints.
- The bounded audit covered 160 episodes / 1,280 visible pairs, 160 finite-rival certificates, 160 30×30 checks, 12 protected-Racket jobs, and 41 unique protected-Racket evaluations with no recorded failures. The declared shortcut bank is finite and is not a proof of unique induction.
- Native qualification passed for both settings at seeds 0 and 17 (4 jobs, 40 protected-Racket labels). The official sequential witness replay changed 54 padded output cells when only Stage A was replaced by union, demonstrating that Stage B consumes the Stage-A intermediate.
- Final staged task suite: 148 passed. Owner-side exact-source integration, fresh qualification/acceptance replay, and any training admission remain pending; current status is `not_accepted`, `training_admitted=false`.
