# Current account: 2da4094bc0e1

## Intended rule and authority

For every maximal horizontal yellow (`4`) run of exactly three cells, replace each immediately adjacent in-bounds background (`0`) cell with magenta (`6`). Preserve the run and every other cell. The selected canonical Racket authority was not changed; `RULE_HASH = 5f2c21d44ce7` pins it.

## Generator v3.0.0

The sampler uses seven exact, observable axes: `grid_h` (8..14), `grid_w` (7..16), `n_bars` (1..3), `n_wrong_bars` (1..3), `n_color_decoys` (1..2), `decoy_color` (5/7/9), and `palette_size` (3/4). Unknown, out-of-domain, boolean, floating-point, and string-coerced overrides fail loudly. Every legal Cartesian combination is constructive; no incompatibilities are declared.

Each returned input contains:

- one to three positive yellow length-3 runs with empty in-bounds cap cells;
- one to three wrong-length yellow runs, including at least one length-4 or length-5 run;
- one or two same-colour non-yellow length-3 runs; and
- for four-colour palettes, one isolated auxiliary-colour cell placed away from every cap position.

These structures distinguish exact length from “at least three” and yellow-specificity from “any same-colour triple.” Dimensions and palette sizes retain broader lawful variation while biasing all three difficulty bands toward the four published `(height, width, palette-size)` profiles.

## Semantic contract

`rule_mirror` is an executable Python mirror checked against the selected Racket output. Declared rivals are:

- `color_agnostic_exact3`: cap every same-colour horizontal run of exactly three;
- `yellow_at_least3`: cap every yellow horizontal run of length at least three.

`color_specificity` and `exact_length` witnesses occur in every ordinary draw. Lessons use three demonstrations and one query; `lesson_identifiable` requires both rivals to be refuted by demonstrations.

## Reversed prior choices

Version 2.1.0 advertised eight mostly dead or singleton texture/palette axes, silently accepted unknown keys, and generated scattered isolated decoy cells. Those cells did not refute the strongest canonical-fitting rival, because they never formed a non-yellow length-3 run. That design was replaced rather than patched: fake texture aliases and degenerate modes were removed, exact structural controls were introduced, and decoys became executable semantic witnesses.

The first v3 candidate still emitted only three-colour inputs and biased hard samples away from canonical profiles. The retained failed battery in `checks/intermediate-after/` showed `canonical_palette_unreachable` and zero hard-band exact-profile hits. `palette_size` plus a safe isolated auxiliary colour repaired both without changing the task rule or either rival witness.

## Evidence

- Final generator SHA-256: `616f2557d331c26df6093031ed6926920e0728328913960546dc1f5159f457e3`.
- Final battery: 12/12 stages green (`checks/final-after/checks/2da4094bc0e1_after_battery_summary.json`).
- Focused/task tests: 39 passed (`checks/task-tests/`).
- Canonical profile floor: 29/60 exact hits, with easy 7/20, medium 8/20, hard 14/20; zero canonical rejections.
- Lesson census: 300/300 production lessons and 1,200/1,200 query rotations identifiable against all declared rivals, with zero materialization or scoring errors (`checks/lesson-census.json`).
- Exact retained counterexample: `counterexamples/color_agnostic_exact3.json`; its selected Racket output is in `checks/final-counterexample/racket.json`.

## Known limits

The generated grammar is intentionally smaller than the complete authority domain: bars are horizontal, have in-bounds empty cap cells, and occupy separate rows; canonical inputs contain richer unrelated vertical clusters and can place multiple target runs on one row. The canonical corpus itself refutes a “one target per row” restriction, but generated lessons do not exercise that morphology. Edge-touching triples and occupied neighboring cells are also not sampled. These are documented distribution limits, not claims about invalid authority inputs.
## Current reviewer considerations

Source SHA-256: `616f2557d331c26df6093031ed6926920e0728328913960546dc1f5159f457e3`.

# Decisions for 2da4094bc0e1

## 1. Preserve the selected authority

**Decision.** Keep the canonical Racket program unchanged and pin its normalized hash as `RULE_HASH = 5f2c21d44ce7`.

**Reason.** All five canonical labeled pairs, the Python mirror, and generated Racket labels agree. The defect was the generator contract and curriculum, not the authority. `rule_smoke`, `racket_lint`, and `authority_sync` are green in the final battery.

**Rejected alternative.** Widening or rewriting the Racket rule would have changed an already supported task merely to accommodate generator metadata defects.

## 2. Replace fake axes with structural, observable controls

**Decision.** Remove palette aliases, texture aliases, singleton position/density controls, and degenerate modes. Advertise only seven controls recoverable from pixels: dimensions, three run counts, decoy colour, and palette size.

**Reason.** The baseline override checker reported 16,729 findings, including dead axes, invalid combinations, 4,590 override mismatches, 9,990 self-check failures, and acceptance of an unknown key. The final checker evaluates 35,190 draws with zero findings or warnings and rejects the unknown-key probe.

**Rejected alternatives.** Keeping compatibility aliases would preserve a public contract that was not executable. Declaring thousands of incompatibilities would document construction failure rather than repair it.

## 3. Make semantic negatives structured, not decorative

**Decision.** Every ordinary input includes a non-yellow exact-length-3 run and a long yellow wrong-length run.

**Reason.** Scattered single decoy cells cannot distinguish “cap any colour triple” from the intended yellow-specific rule. The new objects are direct counterexamples: `color_specificity` refutes `color_agnostic_exact3`, and `exact_length` refutes `yellow_at_least3`.

**Rejected alternatives.** More random noise was rejected because it increases palette variety without changing rival predictions. A lesson-level resampler was unnecessary once every individual draw carries both witnesses.

## 4. Bound counts so the full Cartesian override domain is constructive

**Decision.** Use 1..3 targets, 1..3 wrong-length yellow runs, 1..2 colour decoys, height 8..14, and width 7..16. Place bars on separate rows and keep cap cells in bounds.

**Reason.** The maximum eight bars fit the minimum eight rows; a length-5 run plus two empty neighbors fits width seven. This makes every declared combination legal without hidden vetoes and makes all counts exactly observable.

**Rejected alternatives.** The baseline 1..12 bar count and much wider dimension claims produced impossible combinations. Edge-touching targets were not retained because they make the two-cap lesson less uniform and are not needed to distinguish the named rivals.

## 5. Restore canonical palette and scale support

**Decision.** Add `palette_size=3|4`; four-colour inputs receive one isolated auxiliary-colour cell placed where both horizontal neighbors are background. Bias every band toward canonical 10/11 by 13/14 dimensions, with hard difficulty expressed through more bars rather than only larger grids.

**Reason.** The first repair candidate passed 10 stages but failed distribution and profile gates: its palette was fixed at three colours and hard had 0/20 exact canonical-profile hits. The final profile census has 29/60 exact hits: easy 7, medium 8, hard 14. The auxiliary cell is provably outside every target cap location and does not create a length-3 rival object.

**Rejected alternatives.** A hard band restricted to 12..14 by 14..16 was rejected after the pinned census. Adding an unobservable random colour was rejected in favor of an exact `palette_size` override.

## 6. Keep validation broad enough for canonical inputs

**Decision.** `self_check`/`strict_canonical_like` validate rectangular ARC grids, at least one yellow exact-3 target, at least one wrong-length yellow run, and empty in-bounds target caps, but do not require generated decoy morphology for arbitrary canonical inputs.

**Reason.** All five canonical inputs must remain accepted even though they do not contain the generator's structured blue/gray/maroon triple witness. Semantic witness requirements belong to the sampler/gate, not to authority-domain validity.

## 7. Use executable rivals and three demonstrations

**Decision.** Declare both rivals in `SEMANTIC_RIVALS` and `LESSON_COMPETITORS`, map them to witnesses, declare the canonical-fitting colour-agnostic rival in `CANONICAL_SHORTCUTS`, and set `EXAMPLES_NEEDED = 3`.

**Reason.** Three generated demonstrations plus one query are the production lesson shape. The final semantic smoke test found 12/12 lessons and 48/48 rotations identifiable. The larger source-bound census found 300/300 production lessons and 1,200/1,200 held-out rotations identifiable, with zero errors, under a required-rotation policy.

**Limit.** These finite checks certify only the declared rivals, sampled bands, and recorded schedule; they do not prove uniqueness against every imaginable rule.

## 8. Retain a source-bound exact counterexample

**Decision.** Store `counterexamples/color_agnostic_exact3.json` and test deterministic replay, source hash, Racket-bound intended output, rival output, and exact differing cells.

**Reason.** A prose claim is easy to stale. The retained case ties seed/overrides, generator SHA, selected rule hash, exact input, both predictions, and disagreement cells together.

## 9. Self-review for newly introduced shortcuts

The sampler always uses horizontal bars with empty in-bounds caps and normally separates bars by row. This leaves generated lessons narrower than the authority domain and does not teach edge clipping, occupied-neighbor behavior, or multiple target runs on one row. A canonical input with two yellow triples on one row is a small witness against a hypothetical “at most one target per row” restriction, but generated lessons do not contain that witness. I kept this as an explicit limitation rather than enlarging the contract late, because the selected strongest canonical-fitting rival and both declared discriminator branches are now covered in every draw.


## 10. Replay the exact packaged delta

**Decision.** Extract the packager-generated source patch, apply it to a clean copy of the original upload, verify the resulting generator hash, and rerun the focused suite there.

**Reason.** Tests in the working tree do not by themselves prove that the returned delta is complete or applies cleanly. The retained replay binds original ZIP SHA `92b923a7…41e7`, patch SHA `9138fa92…7cee`, final generator SHA `616f2557…57e3`, and a 39/39 test run.


## Native parametric handoff — review-9832cb58a9be5e67

Built `cap_policy=both_sides|cue_controlled_side`. The default program is byte-exact canonical; the alternative finds the unique red cue, selects the nearest yellow length-4/5 control bar, maps length 4 to left and length 5 to right, and applies that input-derived side to every exact yellow length-3 target. Inputs are deterministic and setting-neutral for 2–6 demonstrations and 1–4 prefix-stable queries, with a distributed 30×30 fourth query.

Finite named-rival audit passed 96 sampled episodes. Native protected-Racket qualification passed 4 jobs / 40 evaluations. The source-bound wrong-intermediate witness substitutes the farthest control on a qualified 30×30 input, reverses the cap side, and changes 32 final cells. Owner acceptance and training admission remain unperformed.
