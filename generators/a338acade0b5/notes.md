# Current notes: a338acade0b5

## Intended rule

A lawful input is a 5..14 by 5..14 grid with exactly two equal nonzero cells.
The cells share a row, share a column, or lie on a 45-degree diagonal. The
output is a one-row cyan bar of inclusive endpoint span
`max(abs(dr), abs(dc)) + 1`, so lengths are 2..14. The selected canonical rule
is pinned by `RULE_HASH = "5661890ac5fd"`; this review did not change it.

## Current generator design

Version 3.0.0 exposes only exact observable controls:

- `segment_length`: integer 2..14;
- `orientation`: `horizontal`, `vertical`, `diag_down`, or `diag_up`;
- `endpoint_color`: integer 1..9.

Malformed/unknown controls fail closed. `self_check` owns the complete declared
input grammar; `strict_canonical_like` intentionally equals that grammar.
Canonical-size red anchors occur in every difficulty band, while a broad slot
varies length, position, color, and dimensions. The broad default length uses a
deterministic residue sweep so the standard production probe covers all 13
finite outputs rather than relying on chance.

## Lesson contract and shortcut defense

The strongest plausible canonical shortcut is `column_span_only`: output
`abs(dc) + 1`. It fits the horizontal and diagonal canonical demonstrations but
fails on a vertical segment. The six-slot schedule is:

1. canonical horizontal;
2. canonical vertical;
3. canonical diagonal-up;
4. broad vertical;
5. canonical diagonal-down;
6. broad vertical.

Lessons use three demonstrations and one query from four consecutive ordered
pairs. Vertical and nonvertical slots alternate, so every cyclic four-pair
window has two vertical pairs, any one-pair query holdout leaves a vertical
demonstration, and both diagonal slopes occur in every schedule period. `SEMANTIC_RIVALS`,
`SEMANTIC_WITNESSES`,
`WITNESS_RIVALS`, `LESSON_COMPETITORS`, and `lesson_identifiable` make this
contract executable.

The minimal retained witness is
`counterexamples/column-span-only.json`: a vertical red span of length 7. The
selected Racket rule returns seven cyan cells; the rival returns one.

## Verification at final source

Final generator SHA-256:
`7ce8cf77ecf3c7c034ac0b5054e6735b54a5a4f3dfeff1e2b49b98118f95e414`.

- after battery: 12/12 stages green;
- portable focused tests: 80/80 passed;
- random lesson census: 300/300 production lessons and 1,200/1,200 query
  rotations identifiable against the declared rival, 484 unique inputs;
- declared-period census at seed 0: 18/18 lessons and 72/72 rotations
  identifiable across easy/medium/hard;
- live rule application and authority synchronization pass.

## Reversed decisions

The imported 2.1.0 design used generic template axes and described painting a
segment into the input. Version 3.0.0 replaces those axes with exact controls
and corrects the output description to a separate one-row bar. A final
self-review also replaced the initial four-slot schedule, which sampled only
one diagonal slope by default, with the six-slot alternating schedule. The change is
based on canonical examples, live selected-rule output, the failed before
battery, and focused RED→GREEN tests; no prior reviewer return was used as a
factual lead.

## Known limits and open findings

The sampler is intentionally structured and nonuniform. Difficulty bands change
default length/dimension support; exact overrides remain valid over their full
advertised domains. The semantic checks are finite and cover the named
`column_span_only` rival, not all conceivable rules. The selected source remains
catalog-unapproved until maintainer intake; passing review checks does not admit
it to training automatically. An archival raw-code authority copy is divergent,
but selected authority execution parity passes and was left unchanged.
## Current reviewer considerations

Source SHA-256: `7ce8cf77ecf3c7c034ac0b5054e6735b54a5a4f3dfeff1e2b49b98118f95e414`.

# Decisions: a338acade0b5

## D1 — Treat the canonical transformation as endpoint-span measurement

**Prior choice:** the imported summary described painting the connecting span
inside the input grid, while the actual canonical outputs are one-row cyan bars.
The rationale for that description is unknown.

**New choice:** require exactly two equal nonzero endpoints aligned horizontally,
vertically, or on a 45-degree diagonal; return a 1×L cyan bar where
`L = max(|dr|, |dc|) + 1`.

**Alternatives considered:** painting the input segment, Manhattan length, and
column-only span. Canonical outputs reject painting and Manhattan length. The
horizontal and diagonal canonical demonstrations do not reject column-only
span, so it remains the explicit plausible rival rather than an alternative
implementation.

**Probe/evidence:** all 3 canonical inputs pass `self_check`; 120/120 live rule
smoke applications match the independent mirror. Rule hash remains
`5661890ac5fd`.

**Failure modes/limits:** this grammar excludes unequal colors, extra objects,
non-straight endpoint pairs, and grids outside 5..14 in either dimension. Those
are deliberate domain boundaries, not extrapolated rule behavior.

## D2 — Replace template axes with three exact observable controls

**Prior choice:** metadata advertised generic `density`, abbreviated
`orientation`, and `position_bias` concepts, while generation materially used
only a texture branch. The original rationale is unknown.

**New choice:** advertise only `segment_length` (2..14), `orientation`
(`horizontal`, `vertical`, `diag_down`, `diag_up`), and `endpoint_color` (1..9).
Each can be recovered from the returned grid by `observe_overrides`.

**Alternatives considered:** preserve a generic texture alias, add public height
and width controls, or keep non-probeable diagnostic axes. Texture added no real
variation; public dimensions would create avoidable compatibility constraints;
diagnostic-only axes would not help downstream sampling.

**Probe/evidence:** focused tests cover length 2, 7, and 14 for every orientation
and every difficulty band. The after override matrix accepted 20,880 exact draws
across 232 cases, rejected unknown keys, and reported no findings or warnings.

**Failure modes/limits:** height and width remain internal and are not exact
public controls. Exact length overrides may exceed a difficulty band's default
range, but still remain within 2..14 and force a fitting grid.

## D3 — Fail closed on malformed inputs, difficulties, and overrides

**Prior choice:** no `self_check` existed and unknown controls could be silently
accepted or ignored.

**New choice:** validate literal rectangular ARC grids, dimensions 5..14,
exactly two equal nonzero endpoints, lawful alignment, and length 2..14. Reject
unknown override names, booleans masquerading as integers, out-of-range values,
and unknown difficulty labels.

**Alternatives considered:** coerce values, ignore unknown fields, or let the
Racket rule fail later. All three hide caller mistakes and make override evidence
unreliable.

**Probe/evidence:** 55/55 destructive mutations were rejected; 3/3 canonical
inputs were accepted; malformed-control regression cases all raise.

**Failure modes/limits:** `self_check` intentionally does not assert a particular
seed, schedule slot, or difficulty-default distribution. It defines lawful task
inputs, not sampler provenance.

## D4 — Use a six-slot alternating curriculum with three vertical slots

**Prior choice:** orientation and dimensions were sampled without a lesson-level
contract, so the canonical-supported `column_span_only` hypothesis could survive
all demonstrations.

**New choice:** repeat six slots in this order:

1. canonical-size horizontal, length 5, red;
2. canonical-size vertical, length 7, red;
3. canonical-size diagonal-up, length 5, red;
4. broad vertical with varying length, dimensions, placement, and color;
5. canonical-size diagonal-down, length 5, red; and
6. a second broad vertical slot.

A lesson is four consecutive pairs, ordered as generated, with any one pair
eligible to become the query and the remaining three retaining order. Vertical
and nonvertical slots alternate, so every cyclic four-pair window has exactly
two vertical pairs, every query rotation leaves a vertical demonstration, and
both diagonal directions appear in every complete schedule period.

**Alternatives considered:** one vertical slot per period, fully random
orientation, rejection-resample until a witness appears, or putting the witness
only in the query. One vertical slot fails under its own holdout; random and
resampling weaken determinism and do not guarantee every lesson; a query-only
witness does not teach the distinction. The first four-slot repair also left
`diag_down` out of default sampling, which the final six-slot design corrects.

**Probe/evidence:** task tests check 8 consecutive starts × 3 seeds × 4 bands and
all four holdouts. The random census found 0/300 production ambiguities and
0/1,200 rotated ambiguities. The period census found 0/18 and 0/72 respectively.

**Failure modes/limits:** the schedule is deliberately structured rather than
i.i.d. The evidence covers `column_span_only`; another undeclared rival could
still fit a finite lesson.

## D5 — Keep canonical anchors in every difficulty band

**Prior choice:** medium and hard had no reliable exact canonical profile in the
20-draw floor check.

**New choice:** three slots preserve canonical grid sizes and red endpoints when
the selected exact geometry fits. Difficulty affects the broad slot's default
length and dimension ranges, not ownership of canonical anchors.

**Alternatives considered:** widen every random draw and hope to hit canonical
profiles, duplicate complete canonical pairs verbatim, or ignore profile-floor
failures. Chance support was the baseline defect; verbatim placement would
narrow spatial diversity; ignoring the floor would leave unsupported canonical
shapes.

**Probe/evidence:** final profile floor records exact canonical-profile hits in
easy, medium, and hard, while placement still varies.

**Failure modes/limits:** anchors intentionally make some marginal distributions
nonuniform. This is curriculum support, not a claim that all lengths or colors
are uniformly distributed.

## D6 — Deterministically sweep the finite output codomain

**Prior choice in the first repair iteration:** the broad slot drew lawful
lengths but the standard 24-episode production probe observed only 10 of 13
possible cyan bars.

**New choice:** for the broad slot, choose the default length from a deterministic
seed/sample-index residue over the active band. Because the standard episode
seed stride is coprime to the 13-value full domain, the probe observes all
lengths 2..14.

**Alternatives considered:** lower the declared codomain, increase the lint sample
budget, or rely on random chance. The rule truly has 13 outputs; a larger probe
would mask rather than repair brittle support; chance makes a finite grammar
needlessly flaky.

**Probe/evidence:** `checks/tdd-codomain-red.log` captured 10/13 before this
change; the focused regression then passed, and standalone/final lint observed
13/13.

**Failure modes/limits:** per-band defaults still use their declared subranges
(easy 2..6, medium 4..10, hard 7..14). Complete 2..14 support in every band is
available through exact override, not claimed as the default marginal.

## D7 — Bind the strongest plausible rival as executable semantics

**Choice:** declare `column_span_only`, a vertical witness, the witness-to-rival
mapping, and a `lesson_identifiable` hook that validates labels and rejects any
lesson whose demonstrations all fit the rival.

**Alternatives considered:** document the shortcut only in prose or depend on
witness frequency. Prose cannot gate lesson construction; frequency does not
show that each demonstration set contains a refutation.

**Probe/evidence:** canonical fit is 2/3, as expected. The retained vertical
length-7 counterexample has intended output 1×7 and rival output 1×1, confirmed
by live `arcpuzzles apply` in `checks/main-counterexample/racket-final.json`.

**Failure modes/limits:** duplicate declaration names in `SEMANTIC_RIVALS` and
`LESSON_COMPETITORS` refer to the same function and appear as two census labels;
this does not add hypothesis coverage. The hook only judges declared rivals.

## D8 — Leave the selected Racket authority unchanged

**Choice:** repair only the Python generator, tests, task notes/summary, and
counterexample. The canonical rule already passed the before rule smoke and
matched all canonical outputs.

**Alternatives considered:** rewrite the Racket implementation to mirror the new
Python helper. That would create authority churn without fixing the observed
sampling and contract defects.

**Probe/evidence:** authority synchronization reports selected source synchronized
and execution parity PASS. The archival raw-code copy remains divergent, a
pre-existing catalog condition rather than a selected-rule failure.

## D9 — Audit targets are evidence-only

The two assigned audit generators were not modified. Each finding is bound to
the assigned generator hash and selected Racket rule output under
`checks/audit/`; proposed repairs belong in those generators' own assignments.
