# Current generator notes: b2387c876b95

## Intended rule and authority

Find the unique complete gray/color-5 row or column. For every red/color-2 cell,
paint the equal-distance point across that divider color 3. Preserve the red
source, divider, background, and unrelated colored object. The selected Racket
authority remains unchanged and is pinned by `RULE_HASH = "d6356bd3481a"`.
The prior summary incorrectly said the reflected copy remained color 2; the
canonical outputs and current summary now correctly say color 3.

## Source-bound defect reproduced

Prior audit `review-c7d4212e8b28d96b:v0001` was used only as a lead, then
reproduced against the assigned baseline SHA-256
`f6553473d53de953e01cb74a095d2aea2c954fb092eb324e39e25b75efdbd0fd`:

- the `orientation` override was ignored;
- 200/200 defaults placed the red source only left of a vertical divider or
  above a horizontal divider;
- 0/200 defaults included the canonical unrelated distractor;
- `self_check` accepted red source cells on both divider sides;
- the canonical `RULE_HASH` was absent.

The retained reproducer is `checks/investigation/baseline-reproduction.json`.
The complete before battery failed lint, defect lint, distribution, and override
stages and retained two semantic/profile advisories.

## Current design decisions

Version 3.0.0 replaces the inherited one-direction sampler with a constructive
sampler. Its public controls are all exact and pixel-observable:

- `grid_h` 9–12 and `grid_w` 10–13, matching the dimensions actually exercised
  by the four exact canonical profiles;
- `orientation`: vertical or horizontal;
- `source_side`: negative (left/above) or positive (right/below);
- `shape_variant`: four L-triomino and eight L/J-tetromino variants;
- `distractor_color`: 4, 6, 7, 8, or 9;
- `distractor_shape`: square, length-3/4 horizontal/vertical bars, or an
  L-triomino orientation.

Unknown keys, Booleans, nonintegers, out-of-range dimensions, and negative
sample indices fail closed. The four-position schedule is declared by
`LESSON_SCHEDULE_PERIOD = 4`; every consecutive four-pair lesson includes both
orientations, both source sides, two triominoes, two tetrominoes, and a non-red
distractor. Profiles 0 and 3 are also constructed to refute the review gate's
row-major `first_object_only` attribution shortcut. Source variant, distractor
color, and distractor shape use independent deterministic cycles rather than a
one-to-one profile lock.

The validator requires exactly one divider, one legal red L shape strictly on
one side, blank in-bounds red mirror destinations, no input color 3, and exactly
one legal distractor. Distractor placement requires at least one blank,
in-bounds reflected distractor cell so the `reflect_all_colored` rival is
observable; other reflected distractor cells may leave the canvas, matching the
canonical domain.

## Executable teaching contract

Declared rivals are:

- `negative_side_only`;
- `vertical_only`;
- `tetromino_only`;
- `reflect_all_colored`;
- `first_object_only`.

Witness predicates cover positive-side sources, horizontal dividers, triomino
sources, non-red distractors, and first-object counterexamples.
`lesson_identifiable` rejects any declared rival that fits all demonstrations
but changes the held-out query. Focused tests
exercise every cyclic query rotation and the entire smallest legal geometry
cross: 2 orientations × 2 sides × 12 source variants × 9 distractor shapes =
432 geometry cases (2,160 when all five distractor colors are included in the
standalone exhaustive probe).

## Retained failures and reversals

- The first four-profile schedule had only one triomino. Query rotation could
  leave only tetromino demonstrations; the schedule was changed to two of each.
- The first independent-looking schedule still locked source variant,
  distractor color, and distractor shape one-to-one. Lint exposed the correlation;
  separate deterministic cycles replaced it.
- The first boundary construction required every reflected distractor cell to
  stay on-canvas. The 8×8 exhaustive probe found 240/2,160 legal combinations
  rejected. A failing regression was added first; the condition now requires
  one observable in-bounds mirror cell, and all 2,160 historical boundary cases
  pass.
- The first final-battery candidate advertised dimensions 8–24 while defaults
  used only the exact canonical envelope, and accepted invalid Boolean/negative
  call scalars. The public dimension domains were narrowed to 9–12 × 10–13 and
  strict call validation was added test-first.
- The first strict searched-rival run found three five-pair windows where
  `generic:first_object_only` fit four demonstrations and failed only on the
  held-out query. The exact easy-band warning (`seed=253315711988339`, start
  `22`, query rotation `1`) became a failing regression before the sampler was
  changed. Profiles 0 and 3 now force spatial counterexamples; a deterministic
  sweep covered 2,048 windows and 10,240 rotations with zero recurrences.

## Limits

The finite contract excludes the five declared rivals, not every conceivable
conditional or template-memorizing rule. Default dimensions intentionally stay
on exact canonical profiles rather than spanning the entire ARC size range.
Distractor families are finite, and the Python `rule_mirror` is an authoring
oracle only; Racket remains label authority. Passing review checks does not by
itself admit generated trajectories to training.

## Final source identity

Generator SHA-256: `4b0e2233f25b2485bfceb9c4ba2d222b8ee205cfccc3951b83f7837665991eb1`.
Final verification commands and evidence are indexed in `WORK/RESULTS.json`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-c7d4212e8b28d96b:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `f6553473d53de953e01cb74a095d2aea2c954fb092eb324e39e25b75efdbd0fd`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Specific dead orientation, left/above-only support, absent distractors and permissive reflection-domain finding on f6553473d53d addressed by accepted 4b0e2233f25b: exact observable orientation/source-side controls, both sides, canonical distractors and strict validator. Reviewer reports 471 task tests, 2160 override crosses, 10240 first-object rotations, 300 lessons/1500 rotations and 12/12 battery. Bounded reviewer evidence, no independent rerun or universal semantic proof.

### Assessment or prior finding

## b2387c876b95

**Issue found: the generated distribution omits task-defining variation and the orientation override is dead.**

Reproduction against the packet source:

- `generate(17, 0, orientation="vertical") == generate(17, 0, orientation="horizontal")` is `True`; orientation is chosen by `rng.choice` instead of a keyed draw named `orientation`.
- Across 30 default draws, every source shape was either **left** of a vertical divider or **above** a horizontal divider. No draw placed the source right/below the divider, although canonical train example 3 places it below and reflects upward. Synthetic data can therefore teach the directional shortcut “copy right/down” instead of reflection.
- Every canonical input also contains an unrelated non-red/non-gray object, while the generator emits only colors 0, 2, and 5. That removes the need to identify the red source among distractors.
- `self_check` accepts a full gray divider with red cells on both sides; it checks only divider count and red presence, not the one-side, in-bounds, blank-destination reflection preconditions.

No fixes were made because audit targets are review-only by contract.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `4b0e2233f25b2485bfceb9c4ba2d222b8ee205cfccc3951b83f7837665991eb1`.

# Decisions for b2387c876b95

## D1 — Preserve the canonical Racket rule

**Inherited state.** The selected authority already produced the canonical
outputs, but the generator omitted its rule pin and the prose summary claimed
the reflected copy remained color 2.

**Decision.** Keep the Racket program unchanged, add
`RULE_HASH = "d6356bd3481a"`, make the Python mirror paint color 3, and correct
the summary.

**Why.** Direct canonical comparisons and rule smoke showed the law was correct;
the defect was generator coverage and documentation, not authority behavior.
Changing the rule would have obscured the actual failure.

## D2 — Replace the dead/random control path with exact observable axes

**Inherited state.** `orientation` was ignored, several requested values were not
recoverable from pixels, and invalid call scalars were accepted.

**Decision.** Expose only `grid_h`, `grid_w`, `orientation`, `source_side`,
`shape_variant`, `distractor_color`, and `distractor_shape`. Every explicit value
is drawn through `GenCtx`, recovered by `observe_overrides`, and checked against
the constructed grid. Unknown axes, Booleans, nonintegers, invalid strings,
out-of-range values, and negative sample indices reject.

**Alternatives rejected.** Silently coercing values or keeping compatibility
aliases would preserve the exact provenance ambiguity that the override contract
is meant to detect.

**Probe.** The task tests cover every individual exact control in all four bands,
and the public override stage exercises the declared cross-product.

## D3 — Match the declared dimension domain to exact canonical profiles

**Initial repair choice.** Dimensions were advertised as 8–24 even though the
four-position default schedule exercised only heights 9–12 and widths 10–13.

**Decision.** Declare and enforce `grid_h=9..12` and `grid_w=10..13`.

**Why.** The profile-floor gate requires recurring exact canonical size/palette
profiles. Expanding defaults to 8–24 merely to satisfy an axis-span detector
would introduce distribution drift; a truthful narrow API preserves both the
canonical prior and exact controls.

**Failure that caused the reversal.** The first final-battery candidate passed
11/12 stages but strict defect lint reported untapped axis spans and invalid
Boolean/negative call scalars. A failing test was added before narrowing the
contract and adding strict validation.

## D4 — Generate both geometric directions constructively

**Decision.** Enumerate legal divider/source placements for both vertical and
horizontal dividers and both negative and positive source sides, requiring all
red mirror destinations to be in bounds and blank.

**Why.** The assigned baseline produced 200/200 sources only left/above the
divider, making “copy right/down” a perfect training shortcut. Constructive
placement makes the requested semantic state exact instead of relying on
rejection sampling.

**Probe.** The smallest declared canvas cross covers 432 combinations:
2 orientations × 2 sides × 12 source variants × 9 distractor shapes. An
additional historical 8×8 probe covers all 2,160 combinations after including
five distractor colors.

## D5 — Restore canonical distractors and vary them independently

**Decision.** Every input includes exactly one unrelated object with color in
`{4,6,7,8,9}` and one of nine block/line/L shapes. Its color and shape use
cycles independent of source variant and semantic profile.

**Why.** Every canonical input contains a non-red object. Without it, a model
never has to learn that only red is reflected. Independent cycles prevent the
object type or color from leaking the source profile.

**Failed intermediate.** Lint found source variant, distractor color, and
distractor shape one-to-one locked by the first four-profile schedule. Separate
cycles removed all pairwise locks while preserving lesson coverage.

## D6 — Require an observable but not fully on-canvas distractor mirror

**Initial repair choice.** Distractor placement required the entire hypothetical
reflection to stay in bounds.

**Decision.** Require at least one in-bounds blank reflected distractor cell, but
allow other hypothetical mirror cells to leave the canvas.

**Why.** One visible counterfactual cell is enough to refute
`reflect_all_colored`; the canonical test itself permits partial off-canvas
mirrors. The stronger condition incorrectly rejected lawful small-canvas
combinations.

**Probe.** The initial 8×8 exhaustive run failed 240/2,160 combinations. A
regression test was added first; the revised condition passes 2,160/2,160.

## D7 — Use a four-pair schedule that survives query rotation

**Decision.** Declare `LESSON_SCHEDULE_PERIOD = 4` and schedule two triomino and
two tetromino sources, both divider orientations, both source sides, and a
non-red distractor in every four-pair window. Profiles 0 and 3 also construct a
spatial counterexample to the gate's `first_object_only` attribution shortcut.

**Why.** Lessons have enough counterevidence for the declared rivals regardless
of which pair is held out as query. The initial schedule had only one triomino,
so holding it out left a `tetromino_only` rival consistent with all
demonstrations. A later strict searched-rival run found three five-pair windows
where the sole first-object counterexample could itself be held out; forcing two
counterexamples per four-profile cycle removes that failure for every cyclic
start without restricting explicit geometry overrides.

**Alternatives rejected.** Treating the production query order as fixed would be
cheaper but fragile to downstream rotation or shuffling. The final contract
supports arbitrary held-out positions against the declared rival set.

## D8 — Encode plausible shortcuts as executable rivals

**Decision.** Declare `negative_side_only`, `vertical_only`, `tetromino_only`,
`reflect_all_colored`, and `first_object_only`, with matching executable
witnesses. `lesson_identifiable` rejects a rival that fits every demonstration
but changes the query.

**Why.** Correct labels are insufficient when the demonstrations teach an easier
wrong rule. Executable rivals turn that data-quality property into a repeatable
test rather than prose.

**Limit.** Passing excludes only these five hypotheses over measured lessons;
it does not prove universal identifiability.

## D9 — Keep reusable probes with the task

**Decision.** Add `workspace/reference_probe.py`, source-bound task tests, and
retained before/intermediate/final evidence. The probe independently extracts
dividers, source side, shape variants, distractors, changed cells, and the
intended output from pixels.

**Why.** Future agents can verify the contract without copying generator
internals or guessing repository paths. The canonical helper fallback preserves
portable task-test execution.

## D10 — Leave audit targets unchanged

The independently assigned audit targets were findings-only. `4e79c276ce9d`
showed no issue under 18 portable tests and strict defect lint. For
`cbf77aa253ac`, a retained Racket-labelled four-pair lesson proves a
`horizontal_only` rival can fit all demonstrations and change the query; its
portable task tests and strict scalar contract also fail. No audit-target source
was edited.
