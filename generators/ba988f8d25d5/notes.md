# Working notes: ba988f8d25d5

## 2026-09-28 source-bound review

Assignment `review-3c3b4d18cfdc8272`, model GPT-6 Astra Pro. Frozen baseline was
version 2.0.1. Its own comment describes the earlier constant-output poison fix;
this review does not claim credit for that historical change. Associated notes
were empty, so motivations not documented in the source are treated as unknown.

The new change removes object/color-identity and clearance shortcuts, introduces
sparse-target versus compact-distractor area inversions, makes ordinary override
values exact, and validates the same monochromatic 4-connectivity as Racket.
Baseline evidence: no bbox-area, 8-connectivity, multicolor-connectivity or
least-color-frequency disagreements in 900 actual-Racket draws. Revised counts
are 333, 320, 445 and 779 of 900 respectively; solid-fill disagreements increase
from 291 to 616. These are finite-cohort facts, not accuracy forecasts.

Canonical program text and all canonical rows are unchanged. Only the selected
archival `racket_target.target_code` was aligned byte-for-byte with its existing
`raw_code` and canonical text; that difference consisted of comments. No Racket
algorithm, verification status, approval hash or shared linter was modified.

The first implementation exposed a contact-placement defect: two independently
oriented shapes may have incompatible boundary supports. Finite fitting D4
orientation search fixed it. The first full after run then caught a legitimate
declared-axis span defect because dimensions only sampled 10..12. A red test and
75/25 narrow/broad scale mixture fixed it. Failed attempts remain in checks.

Acceptance evidence: 42 task tests, 132 repo tests, all 12 after stages, 38,430
accepted override draws, 5/5 canonical inputs accepted, 600/600 semantic-manifold
checks, 5/5 Racket-verified named rival witnesses, 12/12 generated lessons passing
the finite-rival lesson check. None of this proves identifiability against
arbitrary programs or a downstream model improvement.

Known restrictions: unpainted construction regions, unique minimum, target size
at most 7, ordinary count 4..6 (3 only when explicitly requested), no foreign color
inside the target crop, and no nested/interlocking bounding boxes. Medium and
hard have the same marginal target-size and dimension ranges; their layouts use
different keyed streams. The schedule is training-oriented, not a blind i.i.d.
benchmark. Future evaluation should use held-out seeds and independent layout
families, and should not inspect a query's label to choose demonstrations.

Portable probe and audit replay commands are in `workspace/README.md`. Full
trade-offs, exact counterexample and findings-only independent audits are in the
packet-root review documents. Approval remains derived by normal repository
intake; this change does not approve itself.
## Current reviewer considerations

Source SHA-256: `9d0622afa3a9c5fffe60b482761621d266fc8e0164343a83b4615c9d98f3e42b`.

# Decisions and input-distribution ledger

Task `ba988f8d25d5`; assignment `review-3c3b4d18cfdc8272`.
Original motivations below are only claimed when the frozen source states them.
The imported associated-notes file was empty.

## 1. Label authority and object identity

**Before:** Racket already selects monochromatic four-connected objects. The
Python validator traversed all nonzero neighbors irrespective of color. The
sampler's unique colors and clearance hid the mismatch.
**Choice:** Keep canonical Racket untouched; use same-color four-connectivity for
measurements, checks and explicit diagnostic rivals. Labels still execute in
Racket. Align only the selected archival target's comment-different text with
its existing raw/canonical text.
**Alternative:** Change Racket to multicolor connectivity. Rejected: it changes
canonical semantics, and canonical examples already contain touching colors.
**Probe:** All five canonical input/output pairs; 900 revised Racket-labelled
samples; 120 rule-smoke executions; exact authority synchronization test.
**Failure/limit:** Diagnostic mirrors are not an independent label authority.
The portable probe measures their equality to Racket and fails on disagreement.

## 2. Ranking by occupied cells, not rectangle area

**Before:** Smallest objects had 1..4 cells, larger distinct sizes and arbitrary
polyominoes. Source explicitly says this varied outputs after an older
constant-[[2, 2]] poison fix. Why 1..4 was chosen is undocumented.
**Choice:** Include a scheduled sparse L of 5..7 cells and a compact distractor
with one more cell. The L's bbox has area 3(k-2); the compact bbox has smaller
area for k=5, 6, 7. Keep general 1..7 targets and canonical 1..2 targets as well.
**Alternatives:** Merely increase random size bounds (rare witnesses); sample and
reject until a rival fails (unbounded runtime/label selection bias). Chose a
bounded geometric construction with no output-based rejection.
**Probe:** Bounding-box rival fits all 5 canonical pairs, agrees on all 900
baseline draws, and disagrees on 333/900 revised draws. Exact seed/index/input
and actual Racket output are in QUESTION_ANSWER.md and the probe report.
**Failure/limit:** This is not a theorem that the old sampler can never emit a
witness; zero means none in the measured cohort. Explicit target sizes below 5
can disable the scheduled area inversion.

## 3. Colors are not object IDs

**Before:** Each object had a unique sampled nonzero color. Motivation beyond
simple coloring is unknown. This makes per-color frequency equal component size.
**Choice:** Repeat the target's color on a larger, distinct component in contrast
and diagonal profiles, and in 60% of general-profile draws. Preserve nonzero
colors 1..9 and background 0.
**Alternative:** Arbitrary repeated colors anywhere can merge same-color objects,
silently changing the requested counts. Chose regions that keep the repeated
pair non-edge-adjacent, then verify actual component count and minimum size.
**Probe:** Least-total-color-frequency rival: 0/900 baseline disagreements,
779/900 revised; it already fails 2/5 canonical pairs, so it is not presented as
the answer to the canonical-fitting-rival question.
**Failure/limit:** Structured repetition can create new priors. No claim that
these five rivals exhaust what a learner could exploit.

## 4. Contact and connectivity

**Before:** Chebyshev-one clearance separated all objects, stated to keep the
ranking unambiguous. This also makes 4-, 8-, and multicolor connectivity agree.
**Choice:** Different-colored edge contact in contrast profiles; same-color
corner contact in diagonal profiles. Both are unambiguous under Racket's rule.
**Alternative:** Fully free placement and rejection. Rejected for runtime and
exact-override reliability. Finite fitting D4 orientation search resolves edge
support incompatibilities without changing counts or dimensions.
**Probe:** Actual-Racket rival disagreements rise from 0 to 445/900 for multicolor
connectivity and from 0 to 320/900 for same-color 8-connectivity. The latter fits
all canonical pairs; the former fits only 3/5. A first failing contact-placement
test run is retained, followed by its correction.
**Failure/limit:** The construction regions remain a positional prior; it does
not cover arbitrary interlocking or overlapping bounding boxes.

## 5. Exact axes and dimensions

**Before:** Declared grid 6..20 and count 3..6 could be rejected by narrower
band-specific draws. `small_size`, `palette_kind` and helpful texture aliases
were unconsumed. Why those controls were advertised is unknown.
**Choice:** Four ordinary literal-integer controls, exact for every accepted
combination: h/w 10..20, n 3..6, min size 1..7. Default n is 4..6. Reject floats,
bools, numeric strings, unknown keys and inert former aliases. Narrow the
advertised domain instead of claiming support for impossible dense small grids.
**Alternative:** Best-effort clamping or silently fewer objects. Rejected because
it makes intended experimental settings disagree with observed examples.
**Probe:** 38,430 accepted override draws over 427 cases and 3 bands, no declared
combination rejections; additional task tests cover all 10/20 x 10/20 x 3/6 x 1/7
boundary tuples in all four difficulty settings and all three profiles.
**Failure/limit:** This is an intentional versioned interface change: old inert
palette/texture settings now fail explicitly. Valid 3-object cases are supported
on request, not drawn by default. Dimensions below 10 are no longer advertised.

## 6. Canonical scale, diversity, and difficulty

**Before:** Hard samples were 13..16, outside the canonical dimension envelope.
The exact-profile gate observed 1/60 and envelope 11/60; hard had no support.
**Choice:** One keyed 75/25 narrow/broad mixture in every band: dimensions 10..12
or 10..20. Width and height use separate draws within the shared scale mode.
Easy general/diagonal targets favor 1..4; all contrast targets use 5..7. Medium
and hard share marginal size/dimension ranges but have different layout streams.
**Alternative:** Only canonical dimensions. Implemented initially, correctly
rejected by the declared-axis-span gate, and then fixed through a new red test.
**Probe:** Final profile counts: exact 8/60, envelope 47/60; broad dimensions reach
20 in retained tests. No threshold was relaxed.
**Failure/limit:** A generic profile match is not a distribution-distance proof.
Medium/hard are not calibrated model-difficulty estimates.

## 7. Distractors, shape and crop

**Before:** All sizes were distinct; objects 1..4 drove the output. Only the
minimum needs uniqueness under this training interpretation.
**Choice:** Distractors may tie at minimum+1..3; the minimum remains unique. General
objects use bounded connected growth; sparse L witnesses and compact rivals are
purposeful additions. Preserve black cells inside the returned crop. The crop
contains no other color.
**Alternative:** Allow tied minima or nested objects immediately. Rejected for
this pass: those add tie-order and foreign-pixel semantics not needed to fix the
identified defects. Canonical Racket defines more cases than this sampler covers.
**Probe:** Self-check rejects ties for minimum; accepts all five canonical
examples. Solid-fill rival disagreements:291/900 before, 616/900 after. All ordinary
outputs are produced by canonical Racket, not by returning construction metadata.
**Failure/limit:** Only shapes fitting unpainted regions are sampled, target size
is at most 7, and bbox nesting/foreign-color crop cases remain outside support.

## 8. Lessons and rejection policy

**Before:** No semantic contract distinguished diversity from learnable evidence.
**Choice:** Three consecutive draw profiles (contrast, general, diagonal), five
named alternatives, and explicit witness-to-rival mappings. The lesson checker
requires at least 3 valid demonstrations and rejects any rival that survives all
of them. It checks a supplied output for consistency, not to select examples.
**Alternative:** Universally claim identifiability. Rejected: finite examples
cannot rule out every arbitrary program. This is expressly a finite-rival test.
**Probe:**12/12 repository lessons pass; 600/600 strict inputs; 5/5 witness claims
verified against Racket. Task tests check sliding windows, not only index 0.
**Failure/limit:** The guarantee is training-oriented, not i.i.d. benchmark
sampling. Explicit overrides and externally rearranged/rejected draws can break
window coverage; the checker must still run on the actual delivered lesson.

## 9. Validation and negative examples

**Before:** Blank inputs were accepted, tied minima unchecked, colors and row
shapes insufficiently validated; mutation sensitivity was 0/54.
**Choice:** Check literal integer colors 0..9, rectangular 1..30 shape, nonempty
foreground, at least 3 monochromatic components, unique minimum, and clean target
crop. Negative fixtures remain callable but outside ordinary AXES and fail
self_check even when explicitly named.
**Alternative:** Treat a negative texture name as permission to bypass validation.
Rejected: poison probes should test rejection, not gain a metadata exemption.
**Probe:**31/59 destructive mutations rejected after vs 0/54 before; denominators
vary because generated shapes differ. Blank mutations reject 15/15. These rates
are not directly paired sensitivity estimates and not every mutation is invalid.
**Failure/limit:** The checker deliberately describes an input manifold, not every
input on which the Racket program returns some grid.
