# Working notes: f361853c0fcd

## Intended rule

Find the single hollow color-5 rectangular frame. For each non-{0,5} color in
ascending numeric order, fill an interior column only when equal markers occupy
the aligned top and bottom cells; then fill an interior row only when equal
markers occupy the aligned left and right cells. Preserve the canvas, frame, and
border markers. Unmatched, mismatched, and misaligned markers remain inert. The
numeric paint order means the largest color wins at crossings.

The selected Racket authority was not edited. `RULE_HASH` is pinned to
`cffc010305aa`; canonical pairs, an independent Python oracle, and live Racket
applications cover parity.

## Repaired distribution and controls

Version `4.0.0` replaces the inherited decorative/derived axis surface with six
exact observables: `frame_h=7..11`, `frame_w=8..12`, `n_v_only=1..3`,
`n_h_only=1..3`, `n_cross=0..1`, and `n_decoys=0..4`. Unknown, mistyped, or
out-of-range overrides reject loudly. All advertised combinations are
constructive, so `INCOMPATIBLE_OVERRIDE_COMBINATIONS` is empty.

The six-step schedule contains the five canonical canvas/frame/palette profiles
plus one expanded difficulty-dependent profile. Default draws always contain one
cross and two to four decoy cells. The first two decoys reuse one valid color on
opposite borders at different columns; optional side decoys are unmatched or
mismatched. These are lawful under the authority and teach alignment/matching
rather than a special color or off-frame cue.

Color roles are chosen so each default pair also distinguishes global
orientation-priority shortcuts: a high vertical-only color crosses a lower
horizontal color, while a low cross-column color crosses a higher horizontal
color. The other role colors and all positions remain randomized.

## Semantic contract and retained tooling

Declared canonical-fitting shortcuts are `any_border_marker` and
`opposite_anywhere`. Lesson competitors additionally include
`rows_always_win` and `columns_always_win`. `lesson_identifiable` rejects a
three-demo/one-query lesson if any declared rival fits every demo and changes the
query. The retained exact disagreement is
`counterexamples/any_border_marker.json`.

Reusable authoring probes are in `workspace/reference_probe.py` and
`workspace/schedule_probe.py`. They use `reviewer_support.find_root`,
`canonical_path`, and `canonical_pairs`, include an independent oracle, can run
selected-Racket parity, search replayable rival witnesses, and enumerate every
six-step schedule start under every query rotation.

## Evidence and limits

The final required-rotation battery is green in all 12 stages. Focused portable
tests pass 54/54. The source-bound census materialized 300 lessons (three demos
plus one query), checked 1,200 held-out query rotations, and found no ambiguity
against the four declared rivals. The exhaustive task-local schedule probe
checked 1,800 cyclic-start lessons and 7,200 rotations with the same verdict.

These are finite declared-rival checks, not a proof of unique induction against
all possible hypotheses. The validator intentionally limits support to one
frame, positive outer margins, initially empty interiors, one pair position per
color/orientation, one optional cross color, and at most four decoy cells.
Multiple frames, exterior markers, prefilled interiors, and repeated same-color
pairs are outside this training grammar even if the authority has a defined
result.

The first aggregate after battery retained four Racket startup-handshake
timeouts. The exact first input was validator-clean and later succeeded under an
isolated supported apply; a clean isolated battery then completed all 120 live
Racket applications. This was treated as environmental evidence, not a reason to
weaken the generator.

Imported historical notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `bb3a5ba1a206cd43860aed90f9ec7385a903b4daeb6ed2631e4d19de0598c6bc`.

# Decisions — f361853c0fcd

## D1. Replace the decorative ten-axis surface with six exact observables

**Prior choice.** Version 3.1.1 advertised `frame_h`, `frame_w`, `palette_kind`,
`n_v`, `n_h`, `n_cross`, `palette_size`, `position_bias`,
`n_distinct_colors`, `density`, and `texture`. Several were aliases, derived
values, singleton metadata, or invalid negative fixtures. Difficulty-local
bounds also rejected advertised values, unknown keys were accepted, and the
easy path did not record `n_cross` provenance.

**New choice.** Version 4.0.0 exposes only `frame_h`, `frame_w`, `n_v_only`,
`n_h_only`, `n_cross`, and `n_decoys`. Every explicit value is range-checked
without coercing booleans/strings/floats, consumed through `GenCtx`, and
recovered from the realized grid by `observe_overrides`. The full Cartesian
product is constructive, so `INCOMPATIBLE_OVERRIDE_COMBINATIONS` is empty.

**Why.** These are the quantities a reviewer can actually observe and falsify.
Compatibility aliases were rejected because retaining silent or derived knobs
would preserve the baseline contract defect rather than repair it.

## D2. Admit lawful unmatched and misaligned markers

**Prior choice.** Every emitted non-5 border marker belonged to a valid aligned
same-color opposite-side pair. Consequently the plausible rule “every border
marker launches a line” fit all canonical examples and every generated input.
A slightly stronger shortcut—“a color occurring somewhere on both opposite
borders launches lines through all of those positions”—also fit everything.

**New choice.** Defaults contain two to four inert marker cells. The first two
form a same-color top/bottom pair at *different* columns; optional third and
fourth markers occupy opposite side cells without forming a same-color aligned
row pair. Decoy colors reuse valid pair colors, so the distinction is alignment
and matching rather than an artificial new-color cue. Explicit `n_decoys=0..4`
remains supported.

**Why.** The selected rule tests equality at the two aligned endpoints. These
counterexamples are lawful under that rule and directly distinguish the
strongest canonical-fitting rivals. A retained exact witness is
`repo/generators/f361853c0fcd/counterexamples/any_border_marker.json`.

**Rejected alternative.** Adding markers outside the frame or using a special
“decoy color” would make the intended distinction easier but would teach an
unjustified location/palette heuristic.

## D3. Make numeric crossing priority visible in every default draw

The first vertical-only color is chosen above the first horizontal-only color,
which is chosen above the cross color. That single construction creates both
priority counterexamples:

- at a high vertical / lower horizontal crossing, “rows always win” is wrong;
- at a lower cross-column / higher horizontal crossing, “columns always win” is
  wrong.

The remaining role colors are randomized. This preserves color diversity while
ensuring each normal training pair independently refutes both orientation-only
rivals. Numeric order remains semantically meaningful, so arbitrary color-role
permutation was rejected.

## D4. Retain canonical profiles without memorizing only canonical layouts

The six-position schedule contains the five canonical canvas/frame/palette
profiles and one difficulty-dependent expanded profile. Canonical anchors use
one vertical-only, one horizontal-only, and one cross color, plus reused-color
decoys, preserving palette cardinality five. The expanded slot broadens frame
size, margins, counts, and difficulty while every seed still randomizes marker
positions and colors.

This makes profile-floor support deterministic in every band. It is not a claim
that the five public layouts are the complete task domain; the expanded profile
and exact controls cover additional legal compositions.

## D5. Require a fail-closed semantic analyzer

`self_check` now verifies a rectangular integer grid, one color-5 frame,
positive outer margins, zero exterior/interior background, color-5 corners,
nonzero frame borders, unique valid pair positions, supported pair/cross counts,
and decoys that reuse a valid pair color. Malformed grids return diagnostics
rather than raising. `strict_canonical_like` uses the same documented generator
domain so generated counterexamples are not treated as out-of-domain negatives.

The validator deliberately excludes multiple frames, markers outside the frame,
more than one pair position per color/orientation, and filled initial interiors.
Those cases may have a Racket-defined result, but they are outside this repaired
training grammar.

## D6. Keep the selected Racket authority unchanged

The canonical program already implements the written rule and passes all five
canonical pairs. The repair pins its normalized hash `cffc010305aa`, adds an
independent Python oracle and real-Racket parity probe, but does not edit the
canonical ledger or task-local Racket source.

## D7. Use executable rivals and arbitrary query-rotation checks

`CANONICAL_SHORTCUTS` contains `any_border_marker` and
`opposite_anywhere`; both are checked against every canonical pair.
`LESSON_COMPETITORS` additionally contains `rows_always_win` and
`columns_always_win`. Each default pair refutes all four, and
`lesson_identifiable` rejects any lesson where a declared rival fits every demo
but changes the held-out query.

Lessons use three demonstrations plus one query. The task-local schedule probe
checks every cyclic start and every held-out position; the larger source-bound
census checks the production sampler. These finite checks establish only the
reported named-rival result, not universal uniqueness against all conceivable
rules.
