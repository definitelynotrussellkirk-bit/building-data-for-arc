# Current notes: 0f25172eefa4

## Intended rule and authority

Crop the single colored body above the final row. Read every nonzero key cell
left-to-right. Codes `2` and `5` emit the identity crop, code `3` emits a
clockwise quarter-turn, and code `4` emits a 180-degree turn. Preserve duplicate
keys and join the transformed pieces in order with one zero column between them,
using the tallest piece as the output height.

The canonical Racket authority was not changed. `RULE_HASH` remains
`44e21d5003cc`; the selected source is synchronized and the archival `raw_code`
remains textually divergent but execution-equivalent.

## Prior lead consulted

I used the associated notes imported from
`/home/user/Desktop/ARCagi2/reviews/2/incoming_reviews/review_response_gpt-5.6-thinking-arc2_0f25172eefa4_x/RESULTS.json`
as a lead for the 2/5 identity interpretation, duplicate preservation, and the
intentional narrow teaching grammar. I remeasured the pinned packet source rather
than treating those earlier claims as current evidence.

## Reproduced baseline findings

- Baseline generator SHA-256:
  `515d08015a78709364529d4ffa111c1788fe30eb03b2054f339d6fdafe8c15af`.
- Its battery had 11 green stages and one profile-floor advisory; medium and hard
  samples supplied no canonical-size profile in that check.
- Its retained task tests were not portable: the isolated stage passed 342 tests
  and failed one hard-coded canonical path lookup.
- The strongest measured canonical-fitting shortcut was **“code 5 repeats the
  previous transform, using identity when first.”** It fit all 5 canonical pairs.
  Because every inherited generated 5 was first or followed another 5, it
  disagreed on 0/600 sampled defaults.

## Current decisions (version 2.2.0)

1. Keep the rule and narrow generated code set `{2,3,4,5}` unchanged. The Racket
   oracle has broader branches, but they are not established by the canonical
   lessons and remain outside this generator's declared curriculum.
2. Use a six-entry cyclic key schedule. Every three-example demonstration window
   contains a code-5 case after code 3 or 4, so repeat-previous is refuted. Every
   four-pair rotation also retains a refuting demonstration.
3. Add periodic default 5x7 canonical-profile anchors (`sample_index % 4 == 0`)
   when grid dimensions are not explicitly overridden. Exact dimension overrides
   remain authoritative.
4. Declare seven executable lesson competitors and bind every semantic witness to
   at least one rival. The generator rejects a lesson if any declared competitor
   fits all demonstrations and changes the query.
5. Use portable `reviewer_support` canonical helpers in task tests. Do not infer a
   repository root from a fixed `parents[...]` depth.

## Evidence and limits

Final generator SHA-256:
`3d8e048c0a4dae89a8831c3e6a4b8cb4852b1625c61a366d59e252ab99d2f04f`.
The final battery is 12/12 green; 515 portable task tests pass. A 300-lesson
source-bound census (100 per band) materialized 1,200 distinct inputs and found
zero ambiguity in production or in 1,200 held-out query rotations against the
seven declared competitors. An exhaustive small-schedule probe checked all 18
cyclic starts and 72 rotations with zero failures.

The exact code-5 counterexample is retained at
`counterexamples/five-copies-previous.json` and is covered by schedule/window
regressions. These are finite declared-rival checks, not a proof of unique
induction against every program. Explicit overrides can remove a default
canonical-profile anchor from an individual draw; the guarantee applies to the
default four-index schedule. The generator intentionally assumes one connected,
single-color source body and only codes 2–5.
## Current reviewer considerations

Source SHA-256: `3d8e048c0a4dae89a8831c3e6a4b8cb4852b1625c61a366d59e252ab99d2f04f`.

# Decisions — 0f25172eefa4

## D1 — Preserve the canonical rule and the narrow 2–5 teaching grammar

**Inherited choice:** the selected generator teaches only codes 2, 3, 4, and 5,
even though the executable authority has broader branches. The imported prior
review rationale was that the public examples do not establish those branches.

**Decision:** keep the canonical Racket source and `RULE_HASH=44e21d5003cc`
unchanged; do not add codes 6–8 merely because the oracle executes them.

**Alternatives considered:** broaden generation to every executable branch, or
rewrite the rule to the narrower grammar. The first risks unidentifiable lessons;
the second would alter canonical authority without evidence. Rule smoke and
canonical exact tests establish that no authority change is needed.

**Limit:** this generator is evidence only for the 2–5 subdomain.

## D2 — Replace position-confounded code-5 scheduling

**Inherited choice:** alternate 2-family and 5-family sequences, with every 5 at
the beginning. The original rationale was to expose both identity aliases and
refute the old 5-as-horizontal-flip prose. It succeeded at that goal but created
a different position shortcut.

**Measured failure:** “5 repeats the previous transform, identity when first” fit
5/5 canonical pairs and 600/600 inherited defaults. Exact evidence:
`checks/before-shortcut-probe.json`.

**Decision:** retain the alternating families but use `3-3-5-4`, `4-4-5-3`, and
`3-5-4-4` for default 5-family samples. This puts 5 after a nonidentity transform
while retaining adjacent duplicates and all three transform classes.

**Alternatives rejected:** randomize the 5 position without a schedule (could
leave unlucky lessons ambiguous); delete code 5 (would stop teaching a canonical
alias); rely only on 5-as-flip discrimination (does not address stateful rivals).

**Verification:** all 18 cyclic three-demo windows and all 72 held-out rotations
refute repeat-previous. The final 600-draw probe has 300 contrasts.

## D3 — Add periodic canonical-profile anchors without weakening overrides

**Inherited choice:** dimensions were entirely difficulty-driven. The before
battery's strict profile floor had only 3/60 exact-profile hits, all absent in
medium/hard checks.

**Decision:** when neither dimension is explicitly overridden, set `(grid_h,
grid_w)=(5,7)` on every fourth sample index. Explicit dimension overrides win;
if either dimension is supplied, no partial anchor is injected.

**Alternatives rejected:** force all draws to canonical size (destroys scale
diversity); independently anchor one dimension (surprising joint override
semantics); probabilistic weighting (cannot guarantee a four-pair lesson witness).

**Failure mode/limit:** explicitly overridden blocks do not receive the default
window guarantee. The guarantee is schedule-based, not universal over arbitrary
index selection.

## D4 — Declare rivals and bind every witness to a contrast

**First implementation:** added repeat-previous plus existing flip, duplicate,
and separator rivals. The first after battery failed because four branch witnesses
had no named rival; evidence is `checks/after/`.

**Decision:** add wrong mappings for code 2, code 3, and code 4, expose all seven
through `SEMANTIC_RIVALS`/`LESSON_COMPETITORS`, keep repeat-previous as the sole
measured `CANONICAL_SHORTCUT`, and bind all eight witnesses in `WITNESS_RIVALS`.

**Alternative rejected:** mark branch witnesses as informational. That would make
frequency look like semantic evidence without proving a competing rule is
contradicted.

**Verification:** the added contract regression was red before the mappings and
green after; final semantic battery and required-rotation gate pass. This is a
finite competitor set, not a universal uniqueness theorem.

## D5 — Make tests portable and keep the red/green history

**Inherited choice:** the test file inferred canonical data from a fixed path.
Original rationale is unknown.

**Decision:** use `reviewer_support` helpers and the staged generator package.
Add regressions for every cyclic window, every held-out rotation, canonical
profile anchors, exact overrides, source pinning, and all declared rivals.

**Evidence:** initial targeted run: 3 failed / 343 passed; first green: 514 passed;
contract expansion: 1 failed / 514 passed; final green and official stage:
515 passed. All failed receipts are retained under `checks/tdd-*`.

## D6 — Retain exact counterexamples and a reusable independent probe

The selected-task counterexample contains a 5 after code 3 and is checked by the
supported Racket `apply` path. The independent probe reads declarations rather
than duplicating rival names and binds all results to source hashes. This is kept
under `checks/tooling/` rather than shared source because the logic is task-
specific.

## D7 — Audit findings only; no opportunistic repairs

The drawn targets were `b04b767a1685` and `3e68f3e3f66f`. I reproduced a concrete
Racket disagreement for each, ran their batteries/task-test stages, wrote exact
evidence, and left all audited source files unchanged. Repairing either would be
a separate assignment with its own baseline and solve record.
