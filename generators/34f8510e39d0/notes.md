# 34f8510e39d0 — current generator decisions

## Rule and domain

The selected Racket authority (`f97715331ac1`, unchanged) outlines every solid
green (3) rectangle in cyan (8), retaining green interior cells and every
non-green object. Inputs use background 0, isolated solid green rectangles with
both dimensions at least 2 and area at least 6. Other colors retain their fixed
roles; a color-role exchange must be relabeled by the authority, not applied
blindly to a saved output.

## Version 3.1.0 decisions

- **Color and geometry:** prior distractors had area at most 4 while targets had
  area at least 6. A color-blind size selector fit all five canonical pairs and
  all 480 inspected baseline draws. One distractor now copies the largest green
  target's exact oriented shape in every profile, including fallback layouts.
  Thus geometry alone cannot select the target. The remaining small distractor
  in the four-color profile preserves some original variation.
- **Teaching schedule:** the prior three-slot schedule had a single thin-target
  witness in some four-pair windows. Holding it out produced 12 ambiguous query
  rotations in 72 checked rotations. The default period is now four, with
  `thin / A / thin / B`; `EXAMPLES_NEEDED` remains 3. Any single holdout from four
  consecutive default draws leaves a thin witness among three demonstrations.
  Exact `scene_profile` overrides intentionally replace this schedule and carry
  no universal lesson-identifiability guarantee.
- **Rivals:** `outline_rectangles_by_size` is now an executable semantic rival
  and the sole `CANONICAL_SHORTCUTS` entry. The four older rivals remain useful
  lesson competitors but already fail at least one canonical pair.
- **Placement:** retain keyed local RNG, a one-cell gap, random location and
  target orientation, 48 bounded attempts, and lawful deterministic fallbacks.
  Dimensions and palette sizes retain the five canonical profiles. No new axis
  or Racket authority change is introduced.

## Evidence and limits

Focused tests cover actual canonical fit, all profile/band combinations, color
role exchanges, forced fallbacks, all four cyclic starts and every holdout.
`counterexamples/rotation_missing_thin.json` preserves the old missing-witness
lesson. `counterexamples/color_roles/probe-after-final.json` retains the final
480-draw scan (160 unique inputs; each refutes the size rival), replay settings
and input hashes. Its outputs are explicitly Python predictions; the return's
`checks/color-role-racket.json` and `checks/reference-parity.json` verify five
listed cases / four unique inputs against Racket, including a generated role
exchange. The minimal 3x7 authoring witness is validator-lawful but outside the
five strict canonical dimensions.

The final 300-lesson Racket census used three demonstrations and one query:
0 ambiguous production lessons, 0 ambiguous rotations out of 1,200, and 1,168
unique inputs. A separate seed-0 census covered all four start residues in each
band (12 lessons / 48 rotations). These are finite checks against five declared
rivals. Arbitrary hypotheses, joint holdout of multiple queries, other canvas
families, irregular green objects, and color/geometry combinations outside the
declared construction remain unproved.

The three retained current-source audits were used as leads: they found no
issue against the four former declared rivals. They did not examine size-only
selection or every query holdout. Their `needs_triage` records are unchanged;
this repair does not silently resolve unrelated audit status.
## Current reviewer considerations

Source SHA-256: `62d147a5665e372573eb439a63045987b9c016939383e0a6310c542956a6131b`.

# Repair decisions

The immutable draw selected `34f8510e39d0`, assignment `review-40979aa5b9514c87`.
The baseline source was `da8ec3f3ac5ff927b23a00dffe466068134f99e73851d7581ed25f5a14c53bfa`.
Its three retained no-issue audits were used as leads, not new measurements; all
checked the former four rivals and did not test size-only selection or every
held-out query. Their explicit audit statuses remain untouched.

| Choice | Prior rationale / alternative | Decision, evidence and limitation |
| --- | --- | --- |
| Same-size distractor in every scene | Small distractors were intended to refute recoloring all objects, but area separated them perfectly from targets. Random larger distractors only sometimes would leave some lessons uninformative. | Duplicate the largest green target's exact oriented shape in one non-green distractor. All five profile overrides and all fallbacks preserve this. Before 480/480 size-rival agreements; after 0/480. |
| Preserve target colors and authority | The rule assigns fixed meanings to green 3 and cyan 8. A global palette permutation would change task meaning. | Keep reference bytes and fixed colors. Exchange the colors of two matched input objects only as a relabeled counterfactual; actual Racket verifies the changed roles. |
| Four-slot schedule, three demos | The prior thin/A/B cycle teaches ordinary ordered lessons. Increasing demonstrations to five could protect all holdouts but costs two extra examples. | Use thin/A/thin/B with period 4. Every four consecutive default inputs have two thin witnesses, so one holdout leaves one. Retain `EXAMPLES_NEEDED=3`; prove all four starts at seed 0 and test 300 further lessons. |
| Preserve exact profile override | Overriding every draw to an interior-only profile can remove the thin witness. Silently injecting another profile would violate the advertised exact control. | Keep override identity exact and limit rotation guarantee to the default schedule. The lesson hook still rejects insufficient demonstration support. |
| Retain bounded placement | Larger distractors make placement harder. An unbounded loop or shrinking a requested object could conceal failures. | Keep 48 attempts and explicitly update every fallback to the same shape-matching contract. Tests force fallback execution; strict/canonical profile checks remain green. |
| Canonical shortcuts mean canonical fit | Baseline copied all semantic rivals into `CANONICAL_SHORTCUTS`, although each failed at least one canonical pair. | Keep all useful semantic rivals; declare only `outline_rectangles_by_size` as a canonical shortcut. A test checks every declared entry against all five labeled canonical pairs. |
| Reusable probe placement | Shared tools are immutable in this packet. A broad automatic hypothesis generator would exceed this task. | Build a task-owned, portable CPU color-role probe and tests. It records predictions separately from Racket receipts and rejects colliding output destinations. |

## Validation design

Regressions failed before implementation: color support 21 failed / 1 passed;
rotations and canonical classification 7 failed / 6 passed. Both CLI collision
cases also failed before the guard. All 44 final staged cases pass. The after
battery ran with `--require-rotations-identifiable`, not diagnostic-only policy.
The 300-lesson census and exhaustive four-start census use three demos plus one
query, with each pair held out in turn. Observations are against five explicitly
named competitors, not universal identifiability claims.

Five final Racket witness rows contain four unique inputs because one emitted
grid is retained under two witness names. Two rows are the small 3x7 matched
example and its exchange; those are validator-lawful and deliberately not
strict-canonical in dimensions. The generated role exchange supplies canonical
dimension support. `checks/reference-parity.json` records the distinction.

## Remaining scope

The existing five profile families still couple canvas dimensions and target
shape/count. This review does not claim full joint shape/canvas support, new
composition axes, performance gains in a trained model, or training admission.
The inherited public-suite failures and the partial blind solve are retained
with their actual results. No audit-target source or shared fixture is changed
to make unrelated checks green.

# Parametric authoring return — review-9dfada2e459ba31e

The canonical default remains the exact catalog program: outline every solid
green rectangle in cyan. The new episode-fixed `scope` parameter adds
`largest_only`, which first segments the current input's green rectangles,
computes their areas, selects the unique largest rectangle, and then outlines
only that rectangle. Inputs are matched across settings and always contain an
exact-shape non-green distractor, a unique area ranking, four distinct private
queries, and a substantive 30×30 case.

The minimum two-demo prefix refutes the declared opposite-scope, fill-selected,
color-blind-size, and smallest-only rivals. The bounded self-review covered 32
seeds, 320 episodes and 2,560 labeled pairs over every 2–6 demo prefix. The
protected authoring preflight independently replayed four settings/seed jobs and
all labels; the causal witness replaces the inferred largest rectangle with the
smallest and changes the protected Racket output. Public projection checks retain
four controller-side queries privately and expose 16 one-query views, with 24
first-turn invariance checks and four positive controls.

This is reviewer-ready authoring evidence only. Exact-source owner review,
native acceptance and any training admission remain separate.
