# Working notes: caffd29045bc

## Accepted rule

Find the unique full vertical color-9 guide. Preserve the input and copy every
non-{0,9} source cell to the equal-distance column on the opposite side. The
selected Racket authority remains pinned at `RULE_HASH = 71b211cdd7c0`; this
review changes no canonical example or rule source.

## Baseline reviewed

The pinned baseline was generator `2.0.0`, SHA-256
`20769815ea79817629e8ded835c2e683e8bd99a78413c27e6420e30863362c46`.
I used associated note `GNOTE-000961` from prior return
`local-random-88695411e02a` only as a lead for the intended canonical-prior plus
counterexample curriculum, then re-measured the pinned source independently.
The baseline had no executable rival/lesson contract, used a probabilistic
five-step schedule, omitted guide contact as an observable axis, and its focused
tests guessed a fixed repository depth. All canonical examples were centered,
left-sided, connected, and guide-gapped, so four plausible shortcuts fit them.

## Version 3.0.0 design

The production sampler is a deterministic period-four semantic schedule:

1. centered / left / connected / gapped;
2. off-center / right / connected / adjacent;
3. off-center / left / split / adjacent;
4. centered / right / split / gapped.

Lessons use three demonstrations and one query from a four-pair materialization.
Therefore every cyclic start and every query rotation leaves demonstrations that
refute all four declared rivals. Profile 0 cycles exact canonical dimension and
source-count anchors `(7,9,3)`, `(8,11,4)`, `(9,11,4)` independently in every
difficulty band; the other profiles retain generalized geometry. The seven
advertised controls are exact and observable: height, width, source-cell count,
source-color count, side, connectivity layout, and guide contact.

Declared rivals and their required witnesses:

- geometric grid center instead of the color-9 guide -> off-center guide;
- reflect only left-side sources -> right-side source;
- reflect only the largest component -> split source;
- ignore guide-adjacent source cells -> adjacent source.

`workspace/reference_probe.py` checks that all four rivals fit every canonical
label, emits exact counterexamples, and exhausts 16 four-profile windows across
all query rotations. `counterexamples/four-shortcuts.json` is bound to final
generator SHA-256
`3230c13c1f37049ad510d0c209cdbe87786057a698793ff48175e371cd3dc93a`.

## Iteration retained

The first post-repair battery passed 11/12 stages but failed `profile_floor`:
medium and hard had zero exact canonical-profile hits in their 20-draw windows.
I rejected a difficulty-specific opt-out and instead made profile 0 cycle the
three exact canonical anchors in every band. The next profile-floor check and
the final full battery passed.

## Final measurements and limits

Final generator SHA-256:
`3230c13c1f37049ad510d0c209cdbe87786057a698793ff48175e371cd3dc93a`.
The final battery is 12/12 green; the portable task suite has 36 passing cases.
The production census materialized 300/300 four-pair lessons, found 0 production
ambiguities and 0/1,200 ambiguous query rotations against the four declared
rivals, with 1,185 unique inputs. The exhaustive fixed-seed schedule census
checked 12 lessons and 48 rotations with no ambiguity. This is finite evidence
against declared rivals, not a proof against every possible induction rule.
## Current reviewer considerations

Source SHA-256: `3230c13c1f37049ad510d0c209cdbe87786057a698793ff48175e371cd3dc93a`.

# Decisions: caffd29045bc

## D1 — Keep the selected rule and canonical examples unchanged

The selected Racket rule already expresses the intended operation and matched
all canonical outputs. I pinned `RULE_HASH = 71b211cdd7c0`, used an independent
Python mirror only for tests/diagnostics, and did not rewrite canonical,
`target_code`, or archival `raw_code`. This keeps the repair confined to the
teaching distribution and its contracts.

## D2 — Replace the probabilistic five-step prior with a period-four curriculum

The baseline's `sample_index % 5` prior made some generalized examples likely,
but did not state or verify what every complete lesson taught. I chose a period
of four because the assembler uses three demonstrations plus one query: one
profile can be held out while the other three still carry all required semantic
cues. The four profiles are deliberately coupled rather than a Cartesian grid,
which keeps the schedule small enough to exhaust while preserving each needed
contrast.

Rejected alternative: merely increase random probabilities for right, split,
or off-center scenes. Frequency would not guarantee that any particular lesson
or query rotation refuted a shortcut.

## D3 — Add guide contact as an exact axis

All canonical sources are at least two columns from the guide, so a solver can
incorrectly ignore adjacent source cells. `guide_contact=adjacent|gapped` is now
recoverable directly from pixels. Adjacent profiles force both distance-one and
distance-two cells, preventing a degenerate source that only touches the guide.

Rejected alternative: use adjacent cells only as an undocumented random detail.
That would make override and semantic coverage unverifiable.

## D4 — Declare executable rivals, not prose-only risks

The generator exports four pure deterministic rivals: geometric center,
left-source-only, largest-component-only, and skip-guide-adjacent. All fit every
usable canonical pair. `lesson_identifiable` scores the actual demonstrations
and query, while `workspace/reference_probe.py` emits retained exact witnesses.
This makes shortcut claims replayable and keeps future agents from copying a
stale rival-name list.

## D5 — Preserve a canonical profile in every band

The first repaired battery found exact canonical profiles only in easy (3/20),
with 0/20 in medium and 0/20 in hard. I rejected an opt-out and difficulty-based
special case. Profile 0 now cycles the exact public `(height,width,source_count)`
triples `(7,9,3)`, `(8,11,4)`, and `(9,11,4)` regardless of band; generalized
profiles still use difficulty-aware dimensions and counts.

## D6 — Make every advertised control strict and observable

All seven AXES can be reconstructed by `observe_overrides`. Integer overrides
use strict domain checks, string controls use declared choices, unknown keys and
unknown textures raise, and incompatible geometry fails loudly rather than
clamping. No hidden compatibility exceptions were needed.

## D7 — Use portable tests and retain failures

The baseline test guessed a fixed repository depth, which failed portable task
collection. Tests now locate the runtime with `reviewer_support.find_root` and
load canonical pairs through the public helper. The portable preflight failure and the 11/12 profile-floor battery are
retained as evidence rather than overwritten; the focused suite then passed in
the final source and fresh replay.

## D8 — Interpret the semantic result narrowly

The final production census and exhaustive period census establish no ambiguity
against the four declared rivals over the sampled/fixed schedule and all tested
query rotations. They do not prove that no other rival exists. The return uses
`no_ambiguity_found`, not universal-identifiability language.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-60d9c1e6b8f8b049:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `3230c13c1f37049ad510d0c209cdbe87786057a698793ff48175e371cd3dc93a`. At disposition, audited bytes match the current source.

### Current decision

Bounded reviewer-reported clean audit on SHA3230c13c1f37049ad510d0c209cdbe87786057a698793ff48175e371cd3dc93a: 36 portable task tests; all four declared start residues at seed0 in easy/medium/hard, 12 lessons and48 required rotations, no recorded ambiguity/errors. Current generator SHA=3230c13c1f37049ad510d0c209cdbe87786057a698793ff48175e371cd3dc93a. Evidence: checks/audit-caffd29045bc/result.json and checks/audit-caffd29045bc-schedule-period.json. No fresh maintainer execution, other seeds or undeclared rivals are qualified. Preserve this finite assessment in generator notes, not an automatic safety/training admission.

### Assessment or prior finding

## caffd29045bc

**No issue found in the measured scope.** Generator SHA-256: `3230c13c1f37049ad510d0c209cdbe87786057a698793ff48175e371cd3dc93a`. Rule source SHA-256: `71b211cdd7c022ffce4dc9953e1ef48187667af7b6be200fad90839f229a57af`.

The combined audit ran 36 portable task tests: 36 passed, 0 failed/errors/skips. Its semantic stage returned a warning rather than a clean pass because the generator declares `LESSON_SCHEDULE_PERIOD = 4` and the smoke check does not enumerate all starts. The same report nevertheless materialized 12/12 lessons and found 0 ambiguities in 48 diagnostic query rotations against the declared rivals.

I ran the required fixed-seed period follow-up with all four residues across easy/medium/hard and rotation policy `require`. It materialized all 12 expected lessons (48 labelled pairs, 17 unique inputs), with 0 production ambiguities, 0/48 ambiguous rotations, and 0 materialization, hook, or scoring errors. Evidence: `checks/audit-caffd29045bc-schedule-period.json`.

**Scope limit.** This exhausts the declared four-step start residues at schedule seed 0 and the declared rivals. It does not certify every random seed or every undeclared hypothesis. Within the assigned read-only audit scope, I found no concrete defect or surviving declared shortcut, so the target was left unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
