# Working notes: 36275402c6b2

## Current review: `review-6679827af5566d57`

Final generator SHA-256:
`14022562017859a64a23690f41a578166a72b2f153bdecb5b71e0e56c3ffd2a0`.
Version remains `4.1.0`; canonical Racket authority and normalized rule hash
`08894540e7f2` are unchanged. The prior return `review-30f42b66093700f5`
was used as a lead for the established border/side distribution and lesson
contract; its claims were remeasured against this packet rather than assumed.

### Intended rule and retained distribution

The task still crops the unique largest same-colour 4-connected component's
bounding box, reads isolated exterior horizontal pairs as `(replacement,
source)`, and recolours every source-colour cell in the crop. Even sample
indices use the interior-source profile; odd indices provide a non-corner crop-
border source and side legend. Three consecutive accepted examples teach the
rule and the next accepted draw is the query.

### Production repair: exact public-call scalars

The before battery was 11/12 green. `defect_lint` reported 123
`strict-scalar` warnings because legacy `GenCtx` draws accepted or coerced
malformed `seed`, `sample_index`, `difficulty`, and integer override values.
A task-local public-boundary validator now requires non-negative literal integer
seed/index values, the declared difficulty enum, and literal integers for all
six numeric axes. `None` remains the shared no-override sentinel. Unknown axes
are still rejected first, and legal generation is otherwise untouched.

Focused regressions cover malformed booleans, floats, strings, negative call
indices, and the `None` sentinel. A source-paired probe found 100/100 valid calls
byte-identical between the issued and repaired generators. The after battery is
12/12 green and the final portable task-test snapshot is 70/70 green.
`counterexamples/strict-scalar-calls.json` records representative before/after
calls and exact evidence paths.

### Proposed parametric extension (separate from production)

`workspace/parametric/prototype.py` adds one episode-level proposed parameter:
`border_policy ∈ {recolor, preserve}`, with canonical/default `recolor`.
Both settings retain the same largest-component crop, outside-pair roles, and
replacement logic; `preserve` leaves mapped cells on the crop border unchanged.
The default program is the exact canonical Racket text. Four Racket-backed
three-demo/one-query episodes alternate both settings; every demonstration and
query distinguishes the rival setting. Evidence is under
`checks/parametric/border-policy/`. This prototype does not change the selected
production rule, `RULE_HASH`, generator API, or approval state.

### Final evidence and current limits

- Full after battery: 12/12 stages green; the controller-interrupted first
  attempt is retained and the unchanged-source resume completed successfully.
- Final task tests: 70 passed, zero failed/errors/skipped.
- Lesson census: 300/300 lessons materialized across easy/medium/hard, 1,200
  unique inputs, zero production ambiguities, and zero ambiguities in 1,200
  query rotations against the six declared rivals.
- Post-repair visible-only solve: first revision passed all three visible
  examples; earlier rule exposure is disclosed and no reference was consulted
  during the solve.

The repair introduces no new generated-grid restriction; it rejects only
malformed public-call values. Finite declared-rival checks do not prove
identifiability against every possible hypothesis. The parametric evidence uses
only the odd border-and-side profile and four seeds, so it is bounded authoring
evidence rather than a coverage or training-value claim. No unresolved finding
was found in the selected source after this repair.

---

## Retained prior review notes

## Current review: version 4.1.0

Review assignment: `review-30f42b66093700f5`. Generator SHA-256:
`b65d3ab83f95f86f64fee72b91222edf31101a70fb7e1770acaf67b5befc0c58`.

The rule is unchanged: crop the largest same-colour 4-connected component's
bounding box, read isolated exterior horizontal pairs as `(replacement, source)`,
and recolour every source-colour cell in the crop. Canonical examples already
require recolouring on crop borders and reading legends beside the crop; the
previous generator never produced those two witnesses.

Even sample indices retain an interior-source profile. Odd indices place exactly
one source on a noncorner crop-border cell and require a crop-row side legend.
Every source also occurs inside the crop. Legends can occupy any of the four
sides, with one black-cell gap; the crop itself may touch a grid edge. Removing
one noncorner perimeter cell leaves the frame connected through all four corners.
The declared six exact override axes are unchanged.

Three demonstrations are required. A lesson uses three consecutive accepted
draws as demonstrations and the next draw as its query. Holding out any of these
four pairs leaves an odd-profile witness in the remaining demonstrations, for
both cyclic starts of the two-profile schedule. Arbitrary subsampling or shuffling
that discards these witnesses is outside this guarantee.

Legend placement now uses integer suffix counts and rank unranking, rather than
materializing every compatible tuple. For the same ordered slots and no side
constraint, all ranks, outputs, and RNG continuation match the old chooser.
The conditional chooser is uniform over compatible placements containing a side
legend; this is not a claim of uniformity over complete grids.

`self_check` now rejects boolean, float, and string cells in nested numeric
grids instead of silently converting them with `int()`. Null cells remain
rejected. Canonical digit-string rows remain supported. Tests use the public portable root/canonical helpers.

The selected base authority's `racket_target.target_code` was synchronized to the
canonical program's exact whitespace. Canonical ledger bytes, normalized rule
`08894540e7f2`, and archival `raw_code` were preserved; execution is unchanged.

## Evidence retained in the review return

- Final battery: 12/12 stages green, with required query rotations.
- Focused task tests: 29 passed, zero failed/errors/skipped.
- Hard-band joint-axis census: all 7,200 combinations at seed 98173, indices 0
  and 1; 14,400/14,400 grids passed generation, validation, and control checks.
- Racket-labelled lesson census: 100 lessons in each of easy/medium/hard;
  300/300 materialized, 1,200 unique inputs, zero production ambiguities and zero
  ambiguities in 1,200 query rotations against the six distinct declared rivals.
- `counterexamples/border-and-side-witness.json` records an accepted generated
  witness and actual Racket output refuting both newly declared rivals.
- `workspace/axis_census.py` and `workspace/sampler_evidence/` are reusable probes.

The final return's `REVIEW.md`, `DECISIONS.md`, and `RESULTS.json` retain exact
commands, final replay evidence, earlier failures, and interpretation limits.
The memory benchmark measures this environment; it makes no timing assertion.

## Remaining limits

The new border and side conditions are coupled on odd indices, and only one
border source is generated there. Multiple border replacements, independently
varied witness counts, and every possible frame topology are not covered.
Declared-rival and finite-grid checks do not prove universal identifiability or
improved downstream model accuracy. Approval and training admission remain
catalog decisions. Imported historical notes are retained unchanged in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `b65d3ab83f95f86f64fee72b91222edf31101a70fb7e1770acaf67b5befc0c58`.

# Decisions — review-30f42b66093700f5

## R1: expand the generated teaching domain without changing the rule

Canonical inputs show both crop-border sources and legends beside the crop.
The previous implementation excluded both by construction. We add those cases
because the transformation already defines them and canonical examples already
refute the corresponding simplifications; changing the Racket rule to match
the narrower sampler would erase intended behavior.

The even profile keeps interior sources. The odd profile replaces one noncorner
perimeter cell with a source and requires a side legend. Removing one noncorner
pixel leaves the perimeter as a connected path through all four corners, so its
bounding box remains the intended rectangle. For all 4–7 by 4–7 crop dimensions,
the remaining frame exceeds every possible generated same-colour source component.
At least three spare columns are reserved on a side on odd indices; every
advertised joint grid/crop width has at least four spare columns in total.
Each exterior pair has a one-cell black gap from the crop and from conflicting
same-row pairs. Frame placement may touch a grid edge.

Rejected alternatives: random witness injection could leave some lessons with
no witness; replacing several perimeter cells complicates connectivity without
being necessary to close this demonstrated gap; introducing new override axes
would broaden the task contract unnecessarily. The selected repair therefore
retains the six axes and checks all 7,200 combinations on both parities.

The source-border and side-legend conditions are coupled, and the border count
is zero or one. This is an explicit remaining distribution restriction, not a
claim that all canonical-looking arrangements are generated. The source-colour
role remains defined by pair direction, not its numeric colour rank.

## Three demonstrations and query rotation

Production assembly is three consecutive accepted draws as demonstrations,
followed by one query. Either cyclic start of the period-two schedule gives
two odd-profile witnesses in the four-pair bundle. Holding out any one pair
therefore leaves an odd witness in the other three, in their original order.
The focused tests exercise both starts and all held-out positions against the
actual declared competitors. The 300-lesson Racket census tests 100 starts per
band and reports production and rotation separately, both with zero ambiguity.

We do not label these new rivals canonical-fitting shortcuts: each fits 3/5
canonical pairs and is already refuted by two. `CANONICAL_SHORTCUTS` remains
empty, while the six distinct rivals are declared in the semantic and lesson
collections. Arbitrary export-time subsampling or sorting requires a new lesson
check; these results do not certify it.

## R2: counted unranking for compatible legend placements

The old implementation enumerated every compatible pair/triple before choosing
one. A 126-slot probe reached 21,681,400 bytes peak traced memory, and the baseline
override battery hit its 300-second limit. The new implementation precomputes
the next compatible index and suffix placement counts, draws one integer rank,
and reconstructs the corresponding lexicographic placement. The conditioned
table separately counts placements that contain a side slot. For fixed small
pair count, the algorithm uses O(n × k) table space and arithmetic work.

We chose this over retries because it cannot become arbitrarily slow on a rare
valid placement and gives exact conditional uniformity. We rejected an arbitrary
first-fit placement because it would bias geometry and change the RNG contract.
Tests exhaust every rank for all 128 subsets of a seven-slot gapped fixture,
check state continuation, conditioned placements, impossible requests, and a
memory ceiling. The fixed-slot unconditioned behavior matches the old chooser;
version 4.1.0 complete grids intentionally change because candidate geometry and
the distribution changed.

## R3: validation and portable task tests

Accepting `True`, `1.5`, or `"1"` as nested numeric cells disguises malformed
data. The validator now requires actual integer cells in that representation,
while preserving digit-string row support for canonical data. `None` was already
rejected and remains covered by the regression test. This is a narrow boundary fix; unrelated inherited
lesson-hook exception behavior and GenCtx coercion were not expanded.

The existing test's fixed `parents[...]` canonical lookup failed the supported
runtime preflight. It now uses public root discovery and canonical pair APIs.
The new authority regression similarly discovers the canonical data location
through public helpers. Missing isolated pytest was an environment prerequisite
failure, resolved in a local environment without changing shared dependencies.

## R4: exact selected-authority serialization

The canonical program and selected `racket_target.target_code` were semantically
and whitespace-normalization equivalent, but had different exact text. The
authority gate intentionally compares selected copies. We synchronized the
selected target text to the canonical program, instead of weakening the gate
or changing the canonical ledger. The archival `raw_code` is preserved byte for
byte. `checks/authority-formatting-change.json` records old/new hashes; the final
authority file SHA-256 is
`6819067816071488bdbcdbc617675779b0a6d8c4bf18706d4294e9b9093144bb`.
The normalized rule remains `08894540e7f2`; this is an exact-text change to an
authority-bearing file, with no transformation change.

## Audits and tools

A97.1 and A20.1/A20.3 are reproduced control/validator issues. A97.2 and A20.2
are narrower-distribution concerns: normal sampled cases admit a shortcut, and
an authored broader-domain witness distinguishes it from Racket. We explicitly
record whether each witness passes the target validator and whether it belongs
to ordinary generated support. No audit is described as a normal wrong-label
failure. Both audited sources remain byte-identical to their assignments.

The optional ZIP resource preflight lives under `checks/tooling/resource-preflight/`.
It checks metadata and byte/inode capacity without extracting or deleting files.
It neither verifies content checksums nor chooses a destination automatically.
It is separated from the allowed task delta because adopting it in shared packet
tooling requires a maintainer decision.

## Handoff policy

The required final handoff replays the builder's exact source patch against a
fresh verified extraction, initializes an isolated Git root at its `WORK/`
directory (the patch paths begin `repo/`), verifies the actual top-level path,
then reruns focused tests with its own runtime and interpreter. Report changes
after that replay must not alter the source patch; final packaging compares
its patch SHA-256 to the replayed bytes. Failures and genuine solve revisions
are retained; no synthetic failed solve is invented.
