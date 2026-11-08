# Working notes: 1acd7639146e

## Current rule and distribution

The unchanged canonical Racket rule (`RULE_HASH = 695d22e3417f`) treats color 1 as the shared rectangle corner, color 2 as the horizontal endpoint, and color 3 as the vertical endpoint. It paints the complete axis-aligned rectangle outline on a fresh background grid in color 8.

Generator v3.0.0 now samples exactly one marker of each typed color, all four shared-corner orientations, canvas sizes 6..18, rectangle heights and widths 3..6, interior placements, and border/corner contact. Every advertised axis is an exact pixel-observable control. No palette permutations are used because colors 1, 2, 3, and 8 carry fixed semantic roles in the rule.

## Teaching schedule

`EXAMPLES_NEEDED = 4` and `LESSON_SCHEDULE_PERIOD = 4`. Each five-pair window contains one canonical-density slot and three joint-witness slots. The rich slots all use the only orientation absent from the retained canonical examples (bottom-left shared corner) and jointly include border contact, compact dimensions, and extreme aspect ratios. Therefore every single-pair query holdout leaves at least two demonstrations refuting each declared rival.

Declared finite rivals are: only the three canonical orientations, interior-only placement, canonical minimum scale, and near-square rectangles. They are diagnostics, never label authorities; exported labels remain Racket-only.

## Reversed decisions and evidence

- **Prior choice:** v1.1.1 generated only top-left examples and advertised inert palette/texture/density controls. **New choice:** retain only five constructive geometric axes and cover all four orientations. **Reason:** the old distribution allowed several canonical-fitting shortcuts and the control contract was not observable.
- **Early repair hypothesis:** top-right was treated as the missing orientation. **Reversal:** canonical evidence shows top-right is present; bottom-left is the sole unseen orientation. The first focused run retained at `checks/task-tests-green-1/` failed two tests and caused the correction.
- **Rejected alternative:** independent random witness sampling. It can place a sole witness in the held-out query. The fixed cyclic schedule gives redundant witness coverage under every query rotation.

## Retained evidence and limits

- `counterexamples/unseen_bottom_left.json` is a Racket-verified bottom-left witness that refutes the canonical-orientations-only rival.
- `workspace/probe_schedule.py` cheaply enumerates starts and holdouts against declared rivals; it is a Python authoring diagnostic, not a label authority.
- The repair proves coverage only for the declared typed-L domain and finite rival set. It does not establish universal identifiability, behavior with extra markers/distractors, arbitrary colors, rectangles outside 3..6, or canvases outside 6..18.
## Current reviewer considerations

Source SHA-256: `2849a0ba57a96150f31c48156b68156d06fb678496e80cb270f35b01aeaf48e1`.

# Decisions for `1acd7639146e`

## 1. Keep the Racket authority unchanged

**Decision.** Pin `RULE_HASH = 695d22e3417f` and repair only the input distribution.

**Reason.** The canonical examples and direct Racket application agree on a coherent typed-L rule: color 1 is the shared corner, color 2 fixes horizontal reach, color 3 fixes vertical reach, and color 8 forms the complete outline. The defect was missing teaching coverage and false control metadata, not incorrect labels.

**Rejected alternative.** Generalizing the rule to extra markers, distractors, or role-permuted colors. Those cases are not source-bound and would change the task rather than repair its sampler.

## 2. Retain only exact observable controls

**Decision.** Replace palette/texture/density aliases with five exact axes: canvas height/width, rectangle height/width, and shared-corner orientation.

**Reason.** Every value is recoverable from pixels through `observe_overrides`; every declared cross-product is constructive in every band. Unknown/retired keys and non-integer values fail explicitly.

**Ranges.** Canvases are 6..18 and rectangle dimensions are 3..6. A 6x6 canvas supports the maximum rectangle, so no incompatible combinations are needed.

**Failure mode avoided.** The baseline accepted or advertised controls that did not affect returned grids, contaminating metadata-conditioned training and making override sweeps misleading.

## 3. Cover the sole unseen orientation deliberately

**Decision.** Preserve a canonical-density slot using orientations 0, 1, and 3, and make the three rich slots orientation 2 (bottom-left shared corner).

**Reason.** The retained canonical examples contain orientations 0, 1, and 3; orientation 2 is absent. A rival that completes only canonical orientations therefore fits every canonical pair but fails orientation 2.

**Reversal.** The first test version assumed top-right was unseen. `checks/task-tests-green-1/` failed because canonical evidence includes top-right. The source and tests were corrected rather than weakening the assertion.

## 4. Use joint witnesses rather than independent random features

**Decision.** Every rich slot simultaneously supplies bottom-left orientation, border contact, compact scale, and extreme aspect ratio.

**Reason.** Joint witnesses keep the lesson short while refuting four concrete rivals. Independent random draws could omit one feature or place its only witness in the query.

**Rejected alternative.** A probability-only sampler. It can have high marginal feature rates and still produce a locally ambiguous lesson.

## 5. Require four demonstrations and a period-four schedule

**Decision.** `EXAMPLES_NEEDED = 4`, `LESSON_SCHEDULE_PERIOD = 4`, with one canonical slot and three rich slots in every period.

**Reason.** A materialized lesson has five pairs. Under any single-pair query rotation, at least two rich demonstrations remain. This gives redundancy instead of merely one distinguishing example.

**Evidence.** `checks/schedule-census-final.json` exhausts all declared starts at seed 0 across bands; `checks/schedule-probe-32.json` extends the structural check to 32 seeds and finds a minimum of two demo refutations per rival in all 1,920 rotations.

## 6. Keep Python mirrors diagnostic-only

**Decision.** Use independent Python geometry in tests/probes and executable rivals for ambiguity detection, but obtain exported/reference outputs only from Racket.

**Reason.** A Python mirror can validate sampler geometry and expose shortcuts, but it must not silently become a second label authority.

**Evidence.** The retained bottom-left counterexample is labeled by `arcpuzzles apply` in `checks/1acd7639146e-unseen-orientation/racket.json` and is covered by a portable regression test.

## 7. Domain limits

The selected domain requires exactly one each of colors 1, 2, and 3 in typed-L geometry. No claim is made for duplicate/missing markers, extra nonzero colors, palette permutations, rectangles outside 3..6, canvases outside 6..18, or rivals not declared in the source. Finite rival coverage is evidence of improved teachability, not proof of unique induction.

Owner tooling check: `workspace/probe_schedule.py` ran on current generator
`2849a0ba57a96150f31c48156b68156d06fb678496e80cb270f35b01aeaf48e1` with one seed in easy: 4 cyclic lessons /
20 query holdouts, status `pass`. This uses the declared Python
geometry diagnostic, not new Racket labels or a model-learning measurement.
The repository-root command now explicitly includes both local source packages.
