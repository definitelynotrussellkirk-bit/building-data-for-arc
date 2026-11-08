# Current account — 13d2544b2b64, version 3.1.0

Review `review-88cfe058026b16ea` starts from selected version 3.0.0, source
`32ef30f336f32e18aa4c6f02bc473dc2d1f7a5ff309ce3a38cc965fcf6086c6b`.
The prior accepted return `review-aaaca94facfaf522:v0001` was a lead, not new
measurement. Historical counts in the prior notes are superseded by this account.

## Rule and authority

Two zero separator rows and columns partition the input into nine equal panels.
At each local coordinate, equal non-1 left/right sources fill the middle-column
panel; equal non-1 top/bottom sources fill the middle-row panel. Reads use the
original input. Writes may replace occupied targets. Horizontal agreement wins
at a center conflict. Background is 1; markers use colors 2..9.

Canonical Racket is unchanged: `RULE_HASH=301b331591ad`, raw text SHA-256
`a699bbb01d8be15bf86293fdf76bebcf226ebfb019c6968f8917cc74a4f0e0c8`.
No authority, catalog, shared runtime, assignment, or approval was changed.

## Sampler and repaired choices

Production remains 8×8, nine 2×2 panels, separators at rows/columns 2 and 5,
and exactly four colors including 0 and 1. The validator is broader: it accepts
lawful equal panels within the ARC size bound and at least one actual fill.
It does not require every teaching witness on every accepted grid.

The only exact override is `scene_profile`. The four profiles cycle by index:
`canonical_controls`, `equality_mismatch`, `horizontal_precedence`,
`target_overwrite`. `EXAMPLES_NEEDED` is literal `4` because solve preparation
reads it without executing the source; `LESSON_SCHEDULE_PERIOD` declares 4.
Unknown controls are rejected. Both `generate` and `schedule_profile` now require
literal integer seeds and indices, even with an explicit profile. Booleans,
strings, floats and null are rejected; indices must be nonnegative. Signed
integer seeds remain valid.

The prior controls were too dense: retained baseline measurements found their
object/marker-count support disjoint from canonical TRAIN support. Controls now
have five marked cells. The corner-L branch restores fourteen-component /
five-singleton canonical support; the independent branch can have different
component counts. A seeded 50/50 choice
uses either two independent pair fills plus a lone-source control, or a
three-corner same-color L plus a second-color center pair. The latter reproduces
the canonical five-marker topology up to color names. All outer target sides
remain possible. The other profiles retain their original semantic contrasts.

Every generated case still provides both orientations, an outer-middle fill and
a one-sided negative. These are construction guarantees. The prior notes' claim
that `self_check` rejects every missing witness was incorrect and is withdrawn.
The lawful sparse canonical example is accepted by validation.

## Evidence and limits

Final public task tests: **127 passed**, comprising 79 request/distribution
cases, 22 generator/probe cases, and 26 parametric cases. Final fast probe:
1,200 mirror-labelled draws, 1,167 unique, 300/profile, no reported failures,
and no disjoint measured TRAIN structural feature. This restores measured
support; production still omits the sparse two-marker/three-color canonical
example and does not represent the entire canonical distribution. Difficulty
bands select deterministic streams, not a proven difficulty ordering.

Use four consecutive demonstrations followed by query. A Racket-labelled census
of 300 lessons / 1,500 pairs / 1,415 unique inputs has zero ordered production
ambiguities. Enumeration of all four starts at seed 0 across three bands gives
12 lessons and also zero production ambiguities. These are finite declared-rival
checks. Arbitrary query rotation is unsupported: 675/1,500 and 27/60 rotations,
respectively, are ambiguous; moving a sole branch demonstration into the query
slot can remove its teaching evidence.

The final battery is **11/12 stages passing, not an aggregate pass**. Its semantic
stage warns `declared_period_not_enumerated`; the shared receipt loader rejects
the packet-prescribed diagnostic schedule policy. This policy mismatch remains
for maintainer attention. The declaration and failed evidence were preserved.

## Reusable tools and proposed parameter

The probe and tests use `reviewer_support` helpers after an ordinary runtime
reproduced 17/17 baseline path failures; all 22 repaired relocated tests passed.
The probe namespaces all 17 live rival declarations, treats exceptions as
failures, checks parity against all four canonical labels, and measures
structural support against the three TRAIN pairs only. Generated probe labels
are explicitly Python-mirror observations; actual Racket checks are separate.

`counterexamples/review-88cfe058-shortcuts.json` contains exact seed-41 inputs,
actual canonical Racket outputs, and predictions of the three strongest
canonical-fitting shortcuts. The existing focused shortcut test regenerates
those exact cases.

`workspace/parametric/` is a separate **proposed** episode-level parameter:
`crossing_priority` horizontal or vertical. The default is exact canonical
Racket; the alternate only swaps precedence. Two retained episodes teach opposite
settings, each refuting its alternate at demo index 2 before a distinguishing
query. Verification checks a complete nonempty episode inventory and a public
projection without answers or metadata. It has no production API, variant
approval, or training admission.

Final generator SHA-256:
`89e62ab17177d9587fdfa03f593245e3e7eacdacfb388452e03079d61e1fe96e`.
Full commands, failures, rationale and Racket receipts accompany the return.
## Current reviewer considerations

Source SHA-256: `89e62ab17177d9587fdfa03f593245e3e7eacdacfb388452e03079d61e1fe96e`.

# Decisions — review-88cfe058026b16ea

## D1 — Preserve canonical authority and the original reasoning

The selected baseline already bound the mirror to canonical Racket. Retain its
zero separators, background 1, equality matching, occupied-target overwrite,
simultaneous reads and horizontal crossing priority. Production remains nine
2×2 panels in 8×8 inputs with four colors. Larger panels, extra palette axes or
a simplified rule would expand scope without repairing the demonstrated defect.
Final evidence: 120/120 Racket smoke parity and 4/4 canonical acceptance; profile
floor exact/envelope 60/60. This is narrow source-family support, not full shape
or distribution generalization. No authority or approval was changed.

## D2 — Build one meaningful parameter before repairing distribution

The packet prioritized a missing parametric extension. Choose episode-level
`crossing_priority` horizontal/vertical: the default is exact canonical Racket,
and the alternate swaps only two precedence branches. This preserves panel
matching rather than replacing the central rule. A color-only parameter would
be superficial; a changed equality predicate would alter the main reasoning;
a second parameter would enlarge the candidate set without a demonstrated need.

The separate prototype selects once per episode. Seeds 0 and 5 demonstrate both
settings; demo index 2 refutes the alternative before each distinguishing query.
An explicit crossing differs at (3,3), colors 3 versus 9. Build and independent
replay use actual Racket; all four canonical pairs match the default. Public
projection allows only demonstration pairs and query inputs. A discovered empty
report-inventory gap was reproduced by a failing test, then fixed with exact
nonempty contiguous inventory, counts and metadata checks. All 26 tests pass.
The extension remains proposed, two settings and two retained seeds, without
production API, variant approval, or training admission.

## D3 — Require literal reproducible request identities

The baseline accepted booleans, strings and floats as seeds/indices; defect lint
reported 33 scalar warnings. Validate `type(value) is int` in `generate` and
`schedule_profile`, before the override branch. Require nonnegative indices,
while preserving signed and arbitrarily large integer seeds. Coercion can alias
requests silently; banning negative seeds would unnecessarily narrow the valid
domain. Genuine red/green cases cover both entry points, three bands and explicit
overrides. Final defect lint has zero flags.

## D4 — Repair canonical TRAIN support and retain the teaching contrasts

Baseline controls were dense enough that measured object/marker-count support
was disjoint from the three canonical TRAIN examples. Including the labelled
held-out pair could hide this defect. Change only `canonical_controls` to five
marked cells, restoring fourteen-component / five-singleton support through the
corner-L branch. The independent branch may have other component counts. Use a
seeded 50/50 choice between independent
center/outer pair fills plus a lone source, and a same-color three-corner L plus
a different-color center pair. Distinct local coordinates avoid collisions; all
outer target sides remain possible. Other profiles stay unchanged.

The first simple construction repaired feature counts but missed canonical L
topology. A failing geometry regression motivated the second branch. Returning
to dense controls would preserve the known gap. Adding the two-marker canonical
case would require relaxing the existing per-input orientation/outer-control
guarantees, so that larger policy change remains explicit rather than hidden by
a support-score pass. Final 1,200-case probe has 1,167 unique inputs and no
measured disjoint TRAIN structural feature; it does not establish complete
canonical coverage. Production still excludes three-color two-marker inputs.
Bands alter deterministic random streams, not a proven difficulty ordering.

## D5 — Keep four demonstrations and declare the real schedule

The existing four-profile cycle supports four consecutive demonstrations followed
by query. Declare `LESSON_SCHEDULE_PERIOD=4` rather than leave known structure
implicit. The first schedule census correctly failed when no period was declared.
Keep literal `EXAMPLES_NEEDED=4`: solve preparation reads AST literals, so an
intermediate computed value `len(SCENE_PROFILES)` blocked preparation. That
failure was preserved, a regression failed first, and the corrected final solve
is bound to source89e62ab… . It was a preparation failure, not a solve attempt.

The final 300-lesson census and exhaustive fixed-seed four-start census have zero
ordered ambiguities against the declared rivals. Arbitrary holdouts are different:
five materialized pairs have profile counts 2,1,1,1. Removing a singly represented
profile removes its sole teaching demonstration. There are 675/1,500 ambiguous
rotations in the larger census and 27/60 in fixed-seed enumeration. Its 36/60
rotation hook warnings are structurally expected. Another seed cannot eliminate
that missing-profile condition.

The packet allows diagnostic rotation policy for ordered curricula, but the
shared receipt validator only accepts successful blocking rotation evidence.
Without such a receipt the semantic after gate warns that the declared period
is not enumerated. The complete diagnostic receipt is retained, not rewritten.
Removing the declaration would conceal known structure; weakening the hook would
conceal missing demonstrations. A real seven-demo-plus-query policy would supply
two complete cycles, but would change the teaching budget and require new
accepted-instance checks. No downstream arbitrary-rotation requirement justifies
that change here. The return retains the four-demo policy and is blocked for
the shared policy decision described in F1.

## D6 — Distinguish validator scope, construction guarantees and label provenance

The previous notes claimed `self_check` rejects every missing witness. That was
incorrect: lawful sparse canonical inputs are accepted. Current notes separate
sampler guarantees from domain validation. There is no reason to reject every
mutation if the altered input remains lawful.

The fast probe labels generated inputs with the Python mirror. Keep that scope
explicit; use public `arcpuzzles apply`, canonical labels and the battery for
independent Racket evidence. Calibrate support on TRAIN only, while using all
four labelled canonical pairs for parity/shortcut fitting. Namespace all 17
rival declarations, collect exceptions as errors, and never count a crash as a
refutation. Three exact seed-41 Racket witnesses and their rival outputs are
retained; the focused test regenerates those same cases.

## D7 — Build portable tools and verify the transported patch

Repository-depth guesses were masked by the public task-test staging mirrors.
An ordinary `arcpuzzles workspace --id` runtime failed all 17 inherited tests.
Replace guesses with `find_root`, `canonical_pairs` and
`load_selected_generator`; resolve selected Racket through local catalog or
runtime manifest while preserving exact text equality. Repaired relocated
probe/generator tests pass 22 cases; the final public suite passes 127. No frozen
fixture was changed.

A fresh runtime-closure replay checks patch inventory, Git root and exact
changed-file hashes, followed by focused tests in the replay's own interpreter.
The receipt reports partial extraction scope: 340 of 90,295 original files.
All twelve changed-file hashes matched, and the fresh environment passed all
127 task tests with zero failures, errors or skips. Disposable runtime copies are
excluded from the small return, but manifests, failures and command receipts
remain. The bundle preserves all sole copies of failed checks.

## D8 — Keep exposure declarations and stopping state honest

The first solve preceded rule inspection. The post-repair solve is exposed at
overall-review level even though an isolated worker used only visible examples.
Both have one genuine attempt; unknown private query correctness remains unknown.
Logs are human-readable work records, not captured token-level transcripts.
Audit targets receive findings only; their source and admission state stay fixed.

All task-local repair, prototype, tools, counterexamples, tests, solves, audits
and handoff work is delivered. The remaining blocker is the shared receipt
policy. The final battery is 11/12, not a green aggregate; no approval is claimed.
