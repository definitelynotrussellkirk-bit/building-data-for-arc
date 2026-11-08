# Working notes: f563fafba6ac

## Review scope and source identity

Assignment `review-d5e9ac6d3cd9b2e8` reviewed the pinned baseline generator
SHA-256 `6ee5a3426e9fd3c403df643019d0a3449da823a791b1750be83a44cea70c2356`.
No prior return was used as a repair lead; `evidence/associated_notes.jsonl` was
empty. The selected Racket authority was not changed. Final `generator.py`
SHA-256 is `ae0ce7c51dbe8cd9a78e2e44771b8364b523451c7ecaf34253a7f79e1f79d404`
and declares rule hash `458549b829a3`.

## Baseline findings

The before battery retained at `checks/before/` finished 6 green, 1 advisory,
and 5 failed. The generator had no pinned `RULE_HASH`, no executable
`self_check`, no usable semantic contract, no canonical-profile support in each
band, and controls that were missing, dead, or not exactly observable. The old
input distribution also allowed the packed gallery to drift away from the
canonical object grammar.

## Distribution decisions

1. **Three or four objects.** Three-object lessons preserve the canonical
   structure; four-object lessons introduce the two-hole branch. The object
   count is exact and independently observable.
2. **Shape family.** A no-hole width-three solid has area 9–12; a one-hole ring
   is the 3×3 perimeter (area 8); the two-hole object is an 8×3 frame with two
   enclosed vertical regions and area 19. The last value deliberately reaches
   the canonical maximum object area while keeping four packed objects within
   width 15.
3. **Nonexpanding layout.** Bounding boxes are placed with at least one blank row
   or column between them. Random placement is tried first; a deterministic
   one-row fallback is used only when necessary. `self_check` rejects inputs
   whose packed output would exceed the input dimensions.
4. **Colors and order.** Colors are distinct. Descending sampled colors are
   assigned in hole/input order so every ordinary draw refutes color-only
   sorting, leaves equal-hole objects in the wrong reading order, and makes the
   larger no-hole object precede the smaller one-hole ring under the authority.
5. **Canonical support.** With no overrides, every fourth sample index is an
   11×15 or 14×15 three-object anchor. All four exact axes are still drawn and
   recorded on anchor paths; anchors are not provenance-free early returns.
6. **Controls.** `grid_h` is 11..24, `grid_w` is 15..28, `n_objects` is 3..4,
   and `hole_counts` is a list of length 3 or 4 using 0..2 with at least two
   distinct values. Unknown or inconsistent controls raise. No texture axis is
   advertised because there is no independently meaningful texture operation.

## Alternatives rejected

- A smaller two-hole comb was rejected after the intermediate defect lint showed
  that generated objects topped out at area 13 while the canonical maximum is
  19. The retained failed run is `checks/after/`.
- Random color assignment was rejected because it makes shortcut witnesses
  probabilistic rather than curriculum guarantees.
- Treating input position as a harmless nuisance was rejected because two of the
  three canonical pairs are compatible with a stable-input-tie shortcut.
- Adding generic `texture` or `density` controls was rejected: they would be
  labels without a recoverable task-domain meaning.
- Expanding object widths for visual diversity was rejected because it would
  weaken the nonexpanding contract and canonical 15-column support.

## Verification and limits

The final source-bound battery at `checks/after-final/` passed all 12 stages.
Task-local regressions at `checks/task-tests-final/` passed 35/35. The final
semantic gate measured 600/600 strict draws; all three witnesses fired 600/600,
and 12/12 three-demo lessons plus all 48 query rotations had no ambiguity against
the declared rivals. The larger census at `checks/lesson-census.json` retained
300 lessons, 1,200 labelled pairs, and 1,200 held-out rotations with zero
materialization, scoring, or declared-rival ambiguity errors. This is finite
evidence against the three named competitors, not a proof of unique induction
against every conceivable rule or every lesson schedule.
## Current reviewer considerations

Source SHA-256: `ae0ce7c51dbe8cd9a78e2e44771b8364b523451c7ecaf34253a7f79e1f79d404`.

# Decisions for `f563fafba6ac`

## D1 — Preserve the selected authority

**Decision.** Pin `RULE_HASH = "458549b829a3"` and leave canonical Racket data
unchanged.

**Rationale.** Baseline authority smoke and canonical examples were coherent;
the defects were in the generator contract and curriculum. Changing the rule
would have expanded scope without evidence of an authority error.

**Probe.** Final rule smoke applied 120 inputs with 120/120 mirror parity and no
crashes or mutations (`checks/after-final/checks/f563fafba6ac_after_rule_smoke.json`).

**Limitation.** The Python mirror is an independent parity aid, not a replacement
for Racket authority.

## D2 — Make the task domain explicit with four exact controls

**Decision.** Advertise only `grid_h`, `grid_w`, `n_objects`, and `hole_counts`.
Use strict type/range validation, reject unknown axes, and record every default,
anchor, and override path through `GenCtx`.

**Rationale.** These values are recoverable exactly from a returned grid and
materially affect examples. A texture/density axis would have been a nominal
label with no independent task semantics.

**Alternatives rejected.** Silent unknown-key acceptance; axes that only alter
internal sampling; fake texture categories.

**Probe.** The final override matrix covered 285 cases and 25,650 draws with zero
findings. Tests `test_exact_overrides_are_honored_in_every_band` and
`test_default_paths_record_every_exact_axis` cover exact observation and keyed
provenance.

## D3 — Use 3–4 separated objects and a nonexpanding gallery

**Decision.** Produce exactly three or four monochromatic 4-connected objects
whose bounding boxes have at least a one-cell row or column gap. Reject any grid
whose packed output exceeds its input dimensions.

**Rationale.** Three objects retain canonical structure; four objects add the
2-hole branch. Separation makes object extraction unambiguous and keeps input
location a nuisance variable rather than part of the selected rule.

**Alternative rejected.** Wider/free-form shapes gave more visual variety but
made 15-column canonical support and nonexpansion fragile.

**Failure mode.** Random placement can become constrained on minimum canvases;
a deterministic legal fallback prevents stochastic generation failure without
changing the grammar.

## D4 — Choose shapes that distinguish holes from area

**Decision.** Use a solid 0-hole object of area 9–12, a 3×3 one-hole ring of area
8, and an 8×3 two-hole frame of area 19.

**Rationale.** The solid being larger than the ring directly refutes area-first
ordering. Area 19 matches the canonical maximum object size, which defect lint
requires the generalized distribution to reach.

**Rejected intermediate.** A smaller two-hole shape stopped at area 13. The
completed failed battery at `checks/after/` caught this; the regression
`test_hard_draws_reach_the_canonical_largest_object_area` was added before the
19-cell replacement.

**Limitation.** Shape variety is intentionally narrow. The semantic claim is
about ordering by holes, not broad polyomino generalization.

## D5 — Guarantee, rather than merely sample, shortcut witnesses

**Decision.** Assign distinct sampled colors so low-hole objects receive high
colors and equal-hole objects appear in descending color order under input
reading order.

**Rationale.** Each ordinary draw then refutes:

1. `color_only` — colors do not encode primary hole order;
2. `stable_input_ties` — reading order disagrees with the color tie-break; and
3. `area_then_color` — the larger solid must precede the smaller ring.

**Alternative rejected.** Fully random colors/order would make witness coverage
probabilistic and allow weak lessons even when aggregate frequencies looked good.

**Probe.** All three witnesses fired in 600/600 final semantic draws. Each named
rival disagreed on all 60 authority-checked witness samples.

## D6 — Retain canonical profiles in every band

**Decision.** With no overrides, make every fourth sample index an 11×15 or
14×15 three-object anchor while still recording all exact axes.

**Rationale.** The baseline did not hit linked canonical profiles in every
20-draw band check. Deterministic anchors make support reproducible and avoid
seed-luck acceptance.

**Alternative rejected.** A purely weighted prior could still miss a band in a
small pinned check. An early-return anchor was also rejected because it would
skip keyed axis provenance.

**Probe.** Final profile floor found exact hits 7/20 easy, 8/20 medium, and 3/20
hard, with zero canonical rejections.

## D7 — Use three demonstrations and test query rotations

**Decision.** Set `EXAMPLES_NEEDED = 3`; lessons are assembled as three ordered
demonstrations plus one query. Declare the three executable competitors and run
both production scoring and all four held-out query positions for each materialized
lesson.

**Rationale.** The canonical examples themselves leave stable-input and area
shortcuts alive. Every generated grid supplies all required witnesses, so three
demonstrations are adequate against the declared competitor set without padding
lessons.

**Probe.** The final smoke materialized 12/12 identifiable lessons and 48/48
unambiguous rotations. The larger source-bound census materialized 300/300
lessons and found 0/300 production ambiguities and 0/1,200 rotation ambiguities.

**Limitation.** These are finite checks against declared pure/deterministic rivals.
They do not establish unique induction against undeclared rules or every possible
lesson schedule.

## D8 — Keep tests portable and failures visible

**Decision.** Put all new regressions under the selected task’s `tests/` directory,
load canonical data with `reviewer_support.find_root`/`canonical_pairs`, and retain
completed failed iterations rather than replacing them with only final evidence.

**Rationale.** The explicit task-test stage copies tests into an isolated runtime;
fixed parent-depth guesses break there. Failed evidence documents why the final
shape/provenance changes exist.

**Probe.** `checks/task-tests-final/result.json` reports 35 passed, 0 failed,
0 errors, and 0 skipped.
