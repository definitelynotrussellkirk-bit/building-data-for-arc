# Working notes: 4d3c5600ffbd

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `5360812c71c015b1e3befd367bbdaf769e65473648b0ebdc674cd598385927c6`.

# Design decisions — 4d3c5600ffbd

## D1 — Preserve the selected Racket authority

**Decision.** Keep the canonical rule and archival solution unchanged; pin
`RULE_HASH = "af5bd9f68ba9"` in the generator.

**Reason.** All five canonical input/output pairs consistently implement one
component law: recolor a yellow component exactly when it touches two distinct
grid borders. The baseline defects were in generation, validation, controls,
and teaching coverage, not in the selected authority. Rule smoke and authority
sync were green before the repair.

**Rejected alternative.** Rewording or replacing the Racket rule would expand
the review beyond the measured defect and invalidate an otherwise stable
authority chain.

## D2 — Delete fictitious controls instead of simulating them

**Decision.** Replace nine baseline axes with two exact observable axes:
`scene_profile ∈ {canonical_anchor, opposite_span, three_side}` and D4
`transform ∈ 0..7`.

**Reason.** The baseline advertised palette, color-count, position, and texture
variation while always emitting colors 0/4 and essentially the same four
rectangles. Singleton axes (`palette_size`, `position_bias`,
`n_distinct_colors`) could never demonstrate an effect; degenerate textures
were not lawful training cases. A small truthful contract is more useful than a
large metadata surface that silently lies.

**Rejected alternatives.** Keeping `grid_h`/`grid_w` as broad public controls
would either leave canonical support or require a separate semantic geometry
for every size. Keeping palette aliases would be decorative because the rule is
color-specific. Marking singleton controls “diagnostic” would preserve dead API
surface without increasing training value.

**Probe.** `observe_overrides` reconstructs the exact profile and transform from
pixels. The 53-test suite checks every band × profile × transform combination;
the override gate checks the production API independently.

## D3 — Use canonical anchors, not canonical-only replay

**Decision.** Include all five canonical inputs as one schedule role, sampled by
index and D4 transform, but do not make canonical replay the whole distribution.

**Reason.** Anchors preserve natural object sizes and arrangements and guarantee
strict canonical-profile support. Canonical-only replay would preserve two
known ambiguities: `adjacent_two_only` and `at_least_two` both fit every
canonical pair.

**Rejected alternative.** Pure procedural generation without anchors could pass
surface statistics while drifting from real task morphology. Pure canonical
replay would be label-correct but instructionally insufficient.

## D4 — Add the two minimal semantic boundaries

**Decision.** Add an opposite-border positive profile and a three-border
negative profile.

**Reason.** These are the smallest direct counterexamples to the two
canonical-fitting shortcuts:

- an object touching top+bottom or left+right must change, disproving
  “only adjacent-corner objects change”;
- an object touching three borders must remain yellow, disproving “at least two
  borders change.”

Each scene also includes an adjacent positive, one-border negative, and interior
negative so the profile is not a single isolated cue.

**Rejected alternatives.** Four-border negatives are less targeted: they refute
`at_least_two` but do not establish the three-border boundary. Tiny corner-only
templates preserve the original shortcut. Randomly hoping to draw these cases
would make lesson sufficiency probabilistic.

## D5 — Make every five-pair lesson rotation-safe

**Decision.** Use the deterministic profile cycle
`O, T, O, T, C` (`opposite_span`, `three_side`, `canonical_anchor`) with
`EXAMPLES_NEEDED = 4`, yielding five labelled pairs including one query.

**Reason.** With two copies of each decisive profile, holding out any one pair
still leaves an opposite-border witness and a three-border witness in the four
demonstrations. One copy each would fail when that witness became the query.

**Rejected alternatives.** Independent profile sampling can occasionally create
weak lessons. A cycle with one decisive example of each type is not safe under
query rotation. A longer cycle adds complexity without improving the four-demo
teaching guarantee.

**Probe.** `workspace/lesson_schedule_probe.py` checks every held-out position
for all requested cyclic starts and reads rival declarations from the generator,
not a duplicated name list.

## D6 — Keep D4 transforms exact and invertible

**Decision.** Expose all eight square-grid dihedral transforms and define a
canonical orientation for exact observation.

**Reason.** The task is invariant to rotation and reflection. D4 removes fixed
“top-left means target” cues while preserving border-count semantics. Square
canonical profiles avoid dimension-swapping ambiguity.

**Rejected alternative.** Free translations would change which borders an
object touches, so they are not semantics-preserving transforms. Arbitrary
resizing would alter connectivity and canonical morphology.

## D7 — Strengthen validation to task semantics

**Decision.** `self_check` rejects malformed grids, non-rectangular rows,
non-0/4 input colors, answer leakage, wrong dimensions, merged/disconnected
object grammar, absent targets, absent negatives, and missing adjacent targets.
`strict_canonical_like` is a complete pass/fail wrapper for this domain.

**Reason.** The baseline validator only checked whether any yellow touched any
border and accepted all-background-adjacent impostors, small solids, and a full
grid. A validator used in distribution gates must reject structures that do not
exercise the selected rule.

**Rejected alternative.** Treating all-background, all-interior, and full-grid
cases as “degenerate textures” would put examples with no useful positive/
negative contrast in the ordinary training domain.

## D8 — Declare executable rivals and verify their relevance

**Decision.** Export nine pure rival solvers, five witnesses, witness-to-rival
claims, the two canonical shortcuts, and a `lesson_identifiable` hook.

**Reason.** Names alone are not evidence. Tests first establish that the two
claimed canonical shortcuts really fit all five canonical pairs, then establish
that each witness makes the selected rule disagree with its claimed rivals.
The deep census scores these same declarations against source-bound Racket
labels.

**Rejected alternative.** Hard-coding rival names only in a reviewer script can
drift from the generator and falsely certify irrelevant competitors.

## D9 — Key layout variation by difficulty without changing semantics

**Decision.** Keep the same profile contract in every band but include the band
in the keyed scene RNG.

**Reason.** The first repaired attempt was semantically correct but generated the
same 30 sampled inputs across bands. Band-specific RNG creates additional shape
and placement coverage while preserving exact overrides and lesson guarantees.

**Rejected alternative.** Assigning different semantic profiles to different
bands would make lesson quality depend on difficulty and could reintroduce weak
windows.

## D10 — Build a cheap task-local schedule probe

**Decision.** Retain `workspace/lesson_schedule_probe.py` and document its use.

**Reason.** The shared production census rotates queries within sampled lessons
but does not enumerate every possible cyclic start of a short deterministic
schedule. The local probe is fast enough to run after each edit and complements,
rather than replaces, source-bound Racket checks.

**Limit.** It uses the generator’s Python mirror and declared rivals. A bug shared
by those functions could escape it; actual Racket parity tests and the production
census provide independent coverage.

## Remaining restrictions and failure modes

- The domain deliberately stays at canonical sizes (8×8 and 9×9) and colors
  0/4→8; it does not test palette substitution or large-grid extrapolation.
- Synthetic profiles use a finite family of connected objects, including long
  spans and a three-side construction. They do not enumerate all polyominoes.
- Deterministic schedule roles may be statistically recognizable, although D4,
  band-keyed placement, mixed positives/negatives, and canonical anchors reduce
  direct role shortcuts.
- The declared-rival set is finite. Passing it does not prove that no other
  compact wrong program fits a lesson.
- The post-repair visible solve passed all shown examples, but hidden query labels
  remain intentionally unknown to the reviewer.
