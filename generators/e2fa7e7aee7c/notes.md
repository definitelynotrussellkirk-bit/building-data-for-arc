# e2fa7e7aee7c: equal-color midpoint completion

## Current rule and supported domain

The Racket authority remains `f12a9797c652`. Fill a zero exactly between two
equal nonzero cells in one row or column, using the original input for both
directions. This generator uses 2–9 independent motifs, one distinct color per
motif, two endpoints at distance two, and disjoint three-cell footprints.
Default and exact-control grids range from 7×7 to 18×18; every color 1–9 remains
available. The validator also accepts lawful original canonical inputs without
an unequal-color gap. It does not require every valid input to follow the sampler.

## Teaching repair and decision reversal

Version 3.0.0 independently randomized scene orientation and allowed lessons
that never demonstrated why endpoint colors must match. Its retained audit was
reproduced from the exact baseline SHA-256
`2619eac6575b8b836424dd144a4ca5e18ca12ae77afd9467a0b30156cda69d07`:
seed 0, medium, demonstrations 3/4/5, query 6. The color-blind gap filler fits
all demonstrations and incorrectly fills three query cells. The fresh Racket
labels and exact inputs are in `counterexamples/equality-teaching.json`.

Version 4.0.0 constructs a different-color gap on every draw and reserves its
midpoint against ALL true motif footprints. False-gap directions alternate
horizontal/vertical. Default true-orientation modes cycle mixed/horizontal/
vertical/mixed. Default residues 0 and 3 use 7×7 or 8×8, two-motif mixed scenes;
the remaining draws keep difficulty-weighted full ranges. Two canonical-profile
residues replace the prior one-residue schedule after its profile gate warned
at 14/60 envelope hits. The revised gate reports 29/60 exact-profile hits and
30/60 envelope hits, with exact support 11/20 easy, 10/20 medium, 8/20 hard.

The schedule claim applies to ordinary consecutive draws with three
demonstrations and one query. Every four-pair window contains two negative
witnesses per direction and two mixed positive scenes. Any query holdout leaves
both negative directions and at least one mixed scene in the demonstrations.
Explicit controls remain exact; arbitrary filtered/reordered assemblies are
checked against actual labeled pairs by `lesson_identifiable`, rather than
assuming their indices remain consecutive.

## Executable contract and measured evidence

Five competitors cover ignoring color equality globally or on either axis,
and filling only horizontal or only vertical equal-color gaps. The three
color-blind rules fit all three labeled canonical pairs; the new witnesses
refute them. The hook permits answer-equivalent rivals and reports a defect
only if a rival fits every demonstration but changes the query. A witness
excludes an unequal-color gap that coincides with a third motif's true midpoint.

Reviewed generator SHA-256:
`eac8ad9e5856366425b9f03efb2a47e05706bbdbb0ac99fd7acaec8594aa74b1`.
The twelve-stage after battery passed without advisories, including required
query rotations and 42,300 exact-override draws. Focused tests: 15/15 passed.
The public Racket census checked 100 lessons per difficulty: 300 lessons,
1,200 labeled pairs, 1,191 distinct inputs, and 1,200 query rotations, with
zero named-rival ambiguity/errors. Fixed-seed schedule enumeration checked
all four starts in all three bands: 12 overlapping lessons, 48 rotations,
14 distinct inputs, zero ambiguity. A separate dense packing probe passed
600 draws. These are finite observations; see the return's `checks/` receipts.

## Limits and audit disposition

`strict_canonical_like` means lawful independent-pair support; it is not a
claim that every draw has official dimensions/counts. The separate profile
gate reports the latter. Every generated draw now includes an unchanged
different-color gap, a deliberate teaching restriction; ordinary no-distractor
canonical scenes remain validator-supported. There is no theorem against
undeclared rivals, no measured Qwen training improvement, and no guarantee
that 128 randomized packing restarts succeed for every possible seed.

The previously `needs_triage` audit from `review-3400f37203458cb4:v0001` is
addressed by this source and its regressions. After integrating these exact
bytes, the maintainer can explicitly mark that finding resolved, citing this
counterexample and the final census. Its protected review index was not edited
inside this restricted return; generic acceptance must not silently clear it.
## Current reviewer considerations

Source SHA-256: `eac8ad9e5856366425b9f03efb2a47e05706bbdbb0ac99fd7acaec8594aa74b1`.

# Decisions: e2fa7e7aee7c, review-5ecad9cd111a9c71

## D1 — Teach equality without changing the reference operation

The retained ordinary-domain audit was a useful lead, and its exact inputs were
reproduced from the pinned selected source. Fresh public Racket execution shows
the color-blind rival matching demonstrations at indices 3/4/5 and changing
three cells of query 6, seed 0, medium. Evidence:
`checks/repro-before/{replay.json,racket.json,counterexample.json}` and the
task-owned `counterexamples/equality-teaching.json` in the source patch.
The prior archive is not needed to reproduce this finding.

The repair preserves the Racket authority, zero background, unique color per
motif, exact endpoint distance, disjoint footprints, and existing axis domains.
It places two motifs with a different-color zero gap and protects that cell
from every later motif footprint. This supplies a negative example of the
equality condition, while actual same-color gaps still fill.

Rejected: remove all cross-color gaps. That would hide the audited failure
and make the incorrect rival answer-equivalent over the generated domain.
Rejected: increase sparse-scene rejection sampling until an accidental witness
appears. The constructive endpoint relation is cheaper and preserves explicit
size/count controls. Placement locations and motif identities remain randomized;
there is no fixed corner or fixed-color witness marker.

## D2 — Teach both negative directions and positive orientations

The initial design considered forcing a generic negative witness only on even
indices. Independent review showed that a horizontal-only color-blind rival
could survive when its sole refuting example became the query. The final
sampler instead requires a horizontal negative gap on every even index and a
vertical negative gap on every odd index. Positive modes follow M/H/V/M modulo 4.

For ordinary consecutive default draws, any three demonstrations and any
holdout of four pairs retain both negative directions and a mixed positive
scene. `EXAMPLES_NEEDED=3`; `LESSON_SCHEDULE_PERIOD=4`. Five named competitors
cover global/horizontal/vertical color blindness and horizontal-/vertical-only
fill. The three color-blind competitors were checked against all three labeled
canonical pairs and fit them. Names are read dynamically by the public census.

The guarantee concerns this finite rival family and this default assembly.
Explicit orientation overrides may remove one positive branch; filtered,
deduplicated or reordered data must run the hook on actual retained labeled
pairs. The hook rejects a rival only when it fits all demonstrations and changes
the query. Agreement everywhere is allowed. It does not certify every possible
inductive rule.

## D3 — Restore reliable canonical-profile support

The old quarter-rate canonical schedule produced 13/60 exact-profile and 14/60
envelope hits in the actual gate, yielding an advisory below its 25% envelope
threshold. The final sampler uses both mixed-mode residues 0 and 3 for 7×7 or
8×8, exactly two motifs. Other draws retain full difficulty-weighted 7..18
dimensions and 2..9 motif counts. Explicit controls bypass the linked default
profile and remain exact.

Final profile measurements: 29/60 exact, 30/60 envelope; exact hits by band
11/20 easy, 10/20 medium, 8/20 hard. The gate passes without warnings.
`strict_canonical_like` measures the broader lawful independent-pair manifold;
its support fraction is not reported as official-size profile coverage.

## D4 — Verify actual label and lesson behavior

The new regressions first failed on the baseline: 10 failures and 5 existing
passes. An intermediate implementation correctly repaired the lesson but
rejected orientation overrides because the context validates them against the
provided option set. The final call supplies the complete orientation domain
when an explicit mode is requested. The failed intermediate receipt is retained;
the final focused suite passes 15/15.

The full after battery passes 12/12 stages, with required rotation identification,
zero advisories, and 42,300 accepted exact-override draws without findings/errors.
A Racket-labelled census checks 100 lessons per band, starts 0..99 with recorded
per-lesson seeds: 300 lessons, 1,200 pairs, 1,191 distinct inputs, 1,200 rotations,
zero ambiguity/errors/warnings. Fixed seed 0 enumeration covers all four declared
starts in three bands: 12 overlapping lessons, 48 rotations, 14 distinct inputs,
zero ambiguity. These populations are not combined as independent samples.
An independent 600-case 7×7/nine-motif probe checks all three modes and both
negative directions over seeds 0..99. Every actual command and source binding
is retained in `RESULTS.json` and the corresponding evidence.

## D5 — Preserve scope, evidence and honest solve claims

Only the selected generator implementation, summary, notes, tests and minimal
counterexample change. Both assigned audit targets have findings and runnable
reproductions. Shared-tool improvements remain a separate optional proposal.
The protected audit index is not patchable in this packet; the maintainer must
explicitly resolve the old equality finding after integrating the checked source.

The blind solve completed before any generator/reference inspection: one genuine
attempt, 3/3 visible examples. The post-repair solve uses the final generator
hash and discloses earlier exposure: one genuine attempt, 3/3 visible examples.
Both keep private-query correctness unknown. No fabricated negative attempts,
model token traces, training admission or Qwen accuracy improvement are claimed.

The input distribution now always includes at least one negative equality
witness. Original no-witness canonical scenes remain valid under `self_check`.
This is a deliberate teaching restriction, and undeclared size-, palette- or
configuration-specific rivals remain possible. The bounded randomized placement
has an explicit failure path; finite tests do not prove success for every seed.
