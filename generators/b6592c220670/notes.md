# Review notes: b6592c220670

Assignment `review-c583fddb8a070bad`, October 3, 2026. Final source SHA-256:
`5447275c4a8eb23119a9357aa3d8933543d6a801f923152243545dd72c91a3f2`. Imported version `3.0.0` is retained because the immutable retained
fixture asserts it; source identity and compatibility are tracked by the full hash.
Canonical `RULE_HASH=042a7b2c96f6` and all Racket authorities are unchanged.

## Findings and decisions

R1: The four canonical scripts have distinct symbols. Dropping later occurrences
of an instruction is therefore a genuine canonical-fitting rival, unlike the
five old `CANONICAL_SHORTCUTS` entries, which already failed canonical pairs.
The original permutation sampler never generated repetitions. Ordinary scripts
now sample with replacement; the first slot of each four-draw schedule forces a
repeat. Anchor `(2,3,2)` with motif palette `(2,7)` preserves profile `(8,10,4)`
while supplying a nonadjacent-repeat counterexample. Other anchors are unchanged.

R2: The first repaired sampler allowed a four-demo lesson made entirely of
palindromic scripts. The retained counterexample is seed 23008, easy, start 5.
The general first-code-1 slot now ends in code 2. Its first identity panel
contrasts with the first rotated panel under reversal; the existing asymmetric
masks make that contrast observable. This explicit teaching restriction is
preferred to rejection sampling or filtering away a failed lesson after the fact.

R3: Six inherited feature-presence witnesses had no named executable rival.
Each now has one: dropping each of the four operation codes, dropping motif
pixels sharing script colors, or keeping only those colors. All 11 semantic
witnesses are paired with actual answer-disagreement checks; 12 rivals are
registered for lesson checks, and only deduplication is canonical-compatible.

R4: The relocated local test assumed `parents[1]` was the runtime root. It now
uses the same `ROOT` exported by `scripts.canonical_profile_gate`, without editing
frozen fixtures. Twelve new parametrized regression outcomes raise the focused
suite from 18 to 30 tests, including the genuine intermediate order failure.

## Scope and limitations

The prior associated-note lead is `review_response_external-local-random_3c1330db2dfc_x`;
its original return ZIP was not supplied and its ZIP SHA is unknown. Its assertions
were not substituted for a baseline measurement.

Connected compact masks, 4..8 cells, and a four-slot teaching schedule remain.
A disconnected canonical motif is accepted by the validator but is not newly
sampled; general component/cropping induction remains outside this repair.
Exact axis controls still apply; `n_codes=1` deliberately has no repeat guarantee.
Difficulty bands share canonical anchors and must not be pooled as independent
input draws. Approval/training admission is not changed by these checks.

See the returned `REVIEW.md`, `DECISIONS.md`, `QUESTION_ANSWER.md`, full failed
iterations in `checks/`, and `workspace/review_probe.py` for reproducible evidence.
## Current reviewer considerations

Source SHA-256: `5447275c4a8eb23119a9357aa3d8933543d6a801f923152243545dd72c91a3f2`.

# Decisions and rejected alternatives

Source chain: baseline `842b1728813928b7347181f6e96684304d8de3f988e9af3beb6d8d6d098e1183`
→ intermediate `87a0ba32f5b69bdcf1ac46ff41ee619acf0e1f99f971a54423ddc9b14b0a2b95`
→ final `5447275c4a8eb23119a9357aa3d8933543d6a801f923152243545dd72c91a3f2`. All use canonical `042a7b2c96f6`.

## R1: teach repetition without changing the task

**Observed:** all four canonical scripts are distinct-symbol words; the original
general sampler also used permutations. An order-preserving unique-symbol filter
therefore fits 4/4 canonical pairs and all 468 baseline sampled inputs. The
original rationale for excluding repeats is undocumented; do not infer intent
from the code. The existing anchors appear intended to retain canonical size and
palette profiles, which we preserved and measured.

**Chosen:** sample general scripts with replacement, and force a repeated symbol
in slot 0 of the four-slot schedule. A learner must execute each occurrence and
emit each panel. Change only anchor 0 to `(2,3,2)` and palette `(2,7)`; the lost
script color is offset by one new motif color, retaining exact `(8,10,4)` profile.
The repetition is nonadjacent, so it is not merely an adjacent-repeat exercise.
Random general draws also repeat symbols 1, 3 and 4; a dedicated 512-draw hard-band
regression at seed18731 checks coverage of all four identities.

**Rejected:** only declaring a rival without emitting examples; appending an
identical code to every anchor (would alter palette/size balance and teach a fixed
suffix); banning repeats as out-of-domain (contradicts the general script rule);
and accepting the original all-green smoke battery as induction evidence.

**Boundaries:** ordinary no-override lessons contain repeats every four draws.
Exact `n_codes=1` is still lawful and intentionally exempt. No claim is made that
all arbitrary override combinations teach all rivals in four examples.

## R2: fix the real order ambiguity introduced by R1

The first with-replacement implementation allowed the four demo scripts at seed
23008/easy/start5 to be reversal-invariant. Racket receipts and exact five-pair
lesson survive in `checks/counterexamples/reversal-window.json`. Reversing the
script agreed with every demo but changed the query; this was a genuine test
failure, not an intentional negative or a fabricated failed solver attempt.

The general first-code-1 slot now ends in code 2. Since the motif masks are
quarter-turn asymmetric, the identity first panel and reversed-script rotated
first panel differ. Keeping a deterministic witness is simpler and more auditable
than retries, post-hoc lesson filtering, or dropping the failed seed. All eight
cyclic starts are checked so a run need not happen to start at schedule slot zero.

This is a real distribution restriction: the first-code-1 general teaching slot
cannot end in an arbitrary code. We accept that explicit pedagogical schedule
for this bounded repair and do not advertise uniform sampling of all code words.

## R3: preserve witnesses but require executable claims

The first after battery rejected six inherited feature-presence witnesses. We
kept the features and added corresponding answer-changing rivals (skip each code,
discard shared-color motif cells, keep only shared-color cells). Removing the
witnesses or weakening the shared gate would hide the problem. All 11 witnesses
now bind to named callable rivals, while `CANONICAL_SHORTCUTS` contains only the
one rival actually fitting every canonical pair. The other 11 are useful lesson
competitors, not mislabeled canonical-fitting hypotheses.

## R4: portable tests and immutable fixture

The original selected test used filesystem ancestry to locate data. Relocation
changed that ancestry and produced 1 failed/17 passed. Using the exported runtime
`ROOT` beside `canonical_pairs` fixes the test at its actual task-local location.
The frozen root fixture is untouched. Version remains `3.0.0` because that fixture
pins the imported version; full source SHA-256 distinguishes the repair. This is
not a claim that version-only provenance is sufficient.

## Retained input choices

Grid axes 7..16 by 9..20; script length1..6; motif cell count4..8; motif colors1..3;
overlap/disjoint palettes; row-role separation; cumulative transforms; canonical
profile anchors; and compact asymmetric masks are retained. Existing exact-axis
validation remains, and the final override stage reports no errors or warnings.
With at most six panels each at most three columns wide, these masks also keep
ordinary emitted galleries below the ARC width limit; this is specific to the
retained shapes, not a general argument for larger motifs.

The canonical disconnected motif is accepted but not newly sampled. Expanding
component layouts, larger motifs, noise, and arbitrary separator arrangements
would be a different distribution change and require new rivals and tests; none
is silently claimed here. Seed and band overlap are explicitly reported.

## Evidence and reporting

Use independent Racket outputs for the final 468-draw census, not only a mirror
agreeing with its own implementation. Preserve both red rounds and the rejected
intermediate implementation's source-bound receipts. The finite sample is 104
**overlapping** lessons per band, not 104 independent trials. Final public solves
use visible feedback only, with honest exposure and hidden labels still closed.

The associated-note prior return is a navigation lead only; its ZIP hash is
unknown because its bytes were absent. All decisive evidence in this return was
created from this packet. Oversized logs are compressed losslessly, never reduced
to favorable cases or silently deleted. Audited generators remain unchanged.
