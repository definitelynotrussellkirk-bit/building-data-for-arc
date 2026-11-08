# Working notes: 53ffc8bc9584

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Review review-daf200e5ef4d0689 — candidate 2.1.0

The v2.0.0 battery passed all 12 stages, but its examples also fit a wrong rule:
fill a black cell from two perpendicular yellow cardinal neighbors without
checking the diagonal. This rival fits all 3 canonical pairs and survived all
1,200 cyclic lessons plus 300 four-demo/default-index lessons in the retained
baseline probe. Existing rival declarations did not include it.

The sandwich motif now has three isolated yellows in a 2x3 triangle. It exposes
both an opposing-neighbor near miss and perpendicular-neighbor near misses.
It refutes the old two-neighbor rival and the newly registered perpendicular
rival in one scene, preserving EXAMPLES_NEEDED=4 and legacy sandwich acceptance.

The old family schedule also placed every query of the four-demo/default-index
export policy in the isolated family. Family selection now uses (seed+index)%4;
the four-example teaching guarantee survives, and each family gets 25/100
queries per band in the sequential-seed census. Motif orientation uses the
cycle index instead of the family residue, reaching all four orientations.

Malformed values are rejected before set/sort operations. Exact integer
controls reject strings, floats, booleans, and None rather than coercing them.
RULE_HASH remains fbd60dec4738; no Racket or approval source changed.

Final generator SHA256:
0a0ce25730d714988a25b3df83fc8505fd6b8c25278b2f3cf0ba22824b3383f1

Final required battery: 12/12 green. Focused tests: 28 passed. The large probe
found no surviving declared or diagnostic rival across 1,200 cyclic and 300
four-demo/default-index lessons. These are finite, partly overlapping windows;
their input counts and independent-Python versus Racket provenance are retained
in the return's checks/lesson-final/report.json. Do not treat them as 1,500
independent draws or a proof of arbitrary-rule identification.

Bare CLI/API generate still defaults to 3 demos; this shared default does not
satisfy this task's 4-demo contract. Explicitly request 4 demos for training
episodes. Dataset export already defaults to 4. No shared-tool patch is included.

The final solve was exposed to earlier rule work, passed 4/4 visible examples,
and remains unscored on masked queries. The separate blind record must remain
separate. See the return's REVIEW.md, DECISIONS.md, and RESULTS.json for the
compact handoff, retained failed iterations, and exact commands.
## Current reviewer considerations

Source SHA-256: `0a0ce25730d714988a25b3df83fc8505fd6b8c25278b2f3cf0ba22824b3383f1`.

# Decisions — review-daf200e5ef4d0689

This review modifies only task 53ffc8bc9584 and its tests, notes, and workspace
tools. Final generator SHA256 is
`0a0ce25730d714988a25b3df83fc8505fd6b8c25278b2f3cf0ba22824b3383f1`.
Source phases, measurements, and exact commands are in REVIEW.md and RESULTS.json.

## D1 / R1: Teach the missing diagonal explicitly

The prior notes explain why v2 used isolated, linked, sandwich, and colored
families: each noncanonical family refuted one registered shortcut. That was
sound but incomplete. Its opposing-neighbor sandwich did not refute the
perpendicular-neighbor rule. The independent rival fits all three canonical
pairs and every one of the 1,500 baseline lesson windows in the large probe.

The selected repair replaces the ordinary sandwich motif with yellow cells at
local positions (0,0), (0,2), and (1,1), in a 2x3 box, then rotates it. The three
yellows remain separate under cardinal connectivity. They expose one opposing
pair and several perpendicular pairs, but no three-yellow 2x2 trigger. Thus a
single scene refutes both neighbor-count rules. Registering the new rival and a
real witness makes the distinction executable.

Rejected alternatives: a fifth family would increase the ordinary teaching
length; alternating old and new sandwiches would leave some four-demo lessons
without the new witness; adding an independent fifth motif risks tight 7x7
placements. The triangle fits the existing 2x3/3x2 footprint and four-family
structure. Old two-singleton opposing sandwiches remain valid inputs.

The initial hand-built triangle was outside the old validator's domain. This is
a deliberate, limited expansion justified by the unchanged written rule, not
an allegation that the old generator emitted wrong labels. Racket confirms the
triangle is unchanged while true L targets complete. Arbitrary clutter remains
outside the generator's promised domain.

## D2 / R2: Phase family assignment by seed

The original seed-independent family cycle guaranteed all families in four
consecutive demonstrations. Its original rationale was deterministic teaching
coverage; no retained rationale explains the fixed family of the query.

The actual public worker increments the seed across episodes but resets the
starting sample index. With four demos and sample_index=0, the old query was
always index 4 and always isolated. Our initial repair still had this flaw;
three failing query-coverage tests preserve that intermediate result.

Use `(seed + sample_index) % 4` for family selection. This retains the
four-consecutive-family guarantee and distributes a fixed query position across
four consecutive seeds. The isolated and sandwich target-orientation pairs
stay complementary within each lesson. All four seed phases and all 48
structural starts were tested in every band; all 576 lessons pass the hook and
refute all four registered rivals.

Rejected alternatives: requiring every caller to randomize sample_index would
leave the documented default-index path weak; independently randomizing each
sample's family would lose the per-lesson teaching guarantee. Seed phasing is
deterministic and compatible with exact scene_family overrides.

Tradeoff: the four-demo/default-index population changes from 40% strict input
occurrences (two isolated examples in five positions) to 25% on average. The
declared minimum is 20%; the final standard semantic gate measures 141/600
strict hits (23.5%), and the large cyclic/default-index censuses measure 25%.
These are distinct finite populations, not interchangeable estimates.

## D3 / R3: Separate motif variant from family residue

The old family and variant both used sample_index modulo four. As a result,
ordinary linked scenes always used one variant and sandwiches one direction.
This was not justified in the retained notes.

Use the cycle index `sample_index // 4` for the linked and triangle rotations,
while keeping the isolated-L orientation schedule that supplies the lesson's
corner coverage. The final census observes all four linked and triangle
orientations in every band. Random placement alone cannot remove a rotation
shortcut, so translation-only diversity was rejected as insufficient.

## D4 / R4: Return diagnostics for malformed grids

Previously the validator noticed an invalid value but continued into set/sort
operations. Strings and None could trigger mixed-type ordering failures; lists
and dictionaries triggered unhashable-value failures. The caller received a
TypeError instead of validation reasons.

Validate types and allowed values first, retain printable diagnostic values,
and return before structural analysis when invalid cells are present. This
leaves valid-grid semantics unchanged. A broad exception-swallowing wrapper was
rejected because it would hide unrelated implementation defects.

## D5 / R5: Honor exact controls without coercion

The shared GenCtx accepts numeric coercions. That behavior made grid_h=7.9 act
as 7, grid_w="8" act as 8, n_targets=2.9 act as 2, and None alter the scheduled
default. No task-specific rationale supports those conversions for exact axes.

The assigned generator now rejects booleans and noninteger values for integer
controls before calling GenCtx. Unsupported scene families also fail directly.
The shared helper remains unchanged because it serves unrelated generators.
The final 10,080 valid override draws remain exact and observable; focused
regressions separately cover malformed controls.

## D6: Preserve the useful distribution boundaries

Keep dimensions 7..11, canonical square sizes 7/8/9, black background, yellow
trigger color 4, maroon output color 9, two/three true targets, and the existing
non-yellow distractor colors. These are established task-specific choices; the
retained notes do not independently justify every numerical upper bound.

Retain the isolated canonical family and its strict-margin constraints, edge
targets in the other families, and footprint separation. Separation prevents
unintended cross-motif triggers while making the repaired local distinction
legible. Expanding colors, object counts, grid sizes, or arbitrary connectivity
was rejected for this repair because none is needed to demonstrate the found
defects. Such changes would need their own domain and lesson evidence.

Canonical acceptance is 3/3; the final 20-draw per-band profile floor has
11/20 easy, 6/20 medium, and 1/20 hard exact hits. This establishes the required
floor on its pinned census, not a universal per-seed rate.

## D7: Preserve the Racket authority and admission boundary

The selected rule, canonical outputs, and authority synchronization are already
correct. Keep RULE_HASH fbd60dec4738 and all Racket/canonical/catalog/approval
files unchanged. Outputs in the large census use an independent Python
interpretation for speed; actual public Racket episodes and supported apply
batches verify the recorded subset. The Python mirror is never promoted to a
training-label authority.

## D8: Build replayable tools, with honest sampling populations

The lesson probe iterates the actual rival declarations, adds a separately
labeled independent diagnostic, verifies canonical fit, retains source bytes,
and records unique inputs separately from overlapping windows. Its cheap
sampler follows the public worker and was matched exactly on 12 public Racket
episodes for each source. Actual reference checks use the supported apply API.

The later query-family gate was checked with four-seed before/final runs rather
than repeating the entire already-verified Racket workload. Both tool revisions
are retained with source hashes. The portable test launcher gives future agents
a single command for all task-local tests in a copied runtime. Its first
dependency-isolation error and the corrected successful run are both retained.

The four-demo/default-index census matches the explicit task contract and
export's demo default. It is not a bare generate call: bare generate defaults
to three demos, a reproduced shared-tooling gap. Keep that distinction explicit.

## D9: Keep audits and solve records separate

The two random audit targets were drawn unchanged and investigated without
patching them. The ignored palette controls and hard-band profile gap have
source-bound inputs, actual Racket results, and exact command records. Their
repairs belong to separate assignments.

The blind solve was completed before any generator/rule inspection. The
post-repair solve uses final source bytes and honestly declares earlier rule
exposure. Each contains one genuine attempt with a 4/4 visible pass; query
answers remain withheld. We retained the blind fallback ambiguity and did not
manufacture failed solution revisions or claim model training gains.
