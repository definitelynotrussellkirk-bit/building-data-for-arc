# Current notes: `dfa9d0b2dd41`

## Intended rule

Find every nonzero same-color 4-connected object. For each object, crop its bounding box. Sort objects by occupied-cell count ascending, then by top row and left column. Pack the nonzero crop cells left-to-right, top aligned, with one zero column between crops. The existing Racket authority is unchanged and pinned by `RULE_HASH = "76c3cefee423"`.

## Current generator (`2.0.0`)

- Exact controls: `grid_h=8..14`, `grid_w=10..18`, `n_objs=2..4`.
- Every legal combination is constructively feasible; unknown, retired, out-of-range, boolean, string, and nonintegral controls reject.
- Objects use distinct colors, distinct occupied-cell counts, and a one-cell eight-neighbor moat.
- Default schedule repeats one `solid_rectangles` profile followed by two `bbox_area_witness` profiles.
- Solid anchors preserve the canonical rectangle manifold and exact canonical dimension/object-count profiles in every band.
- Witness profiles include a five-cell L with bounding-box area 9 and a six-cell rectangle with area 6, so occupied-cell and bbox-area sorting disagree.
- Shapes, colors, slots, orientations, and global offsets are shuffled independently.

## Reversed decisions

The prior `1.1.0` generator used a rejection sampler, advertised narrowed/inert/constant axes, had no rule pin or semantic contract, and did not guarantee the strongest canonical-fitting rival was refuted. Those controls were removed rather than retained as silent compatibility aliases. Placement is now constructive and the curriculum schedule—not random luck—guarantees witness support.

An intermediate repair capped ordinary objects at six cells. Defect lint showed that this missed canonical scale, so solid profiles now reach nine cells and witness profiles retain a nine-cell object when object count permits.

## Semantic contract and retained witness

The declared canonical shortcut/rival is `bbox_area_sort`. It matches all four labeled canonical pairs because their objects are solid rectangles. The exact generated disagreement, independent outputs, source hash, and authority replay are in `counterexamples/bbox_area_sort.json`; it is covered by the task tests.

`EXAMPLES_NEEDED=3`. With three demonstrations plus one query, any four consecutive scheduled pairs retain at least one bbox-area witness under every query holdout. The final census checked 100 lessons per band, 1,200 pairs, and all 1,200 query rotations with no declared-rival ambiguity.

## Known limits

- The contract is finite evidence against named rivals, not proof that demonstrations uniquely determine the rule among all programs.
- Generated components fit `3×3` slots and object count is capped at four; the authority's mathematical domain is broader.
- Default largest objects reach nine cells; one canonical object reaches ten.
- Palette and placement vary but are intentionally not override axes.
- Query-rotation support is established for the current three-demo/one-query consecutive assembly and declared rivals; other lesson sizes/policies require new checks.

## Evidence and status

- Final generator SHA-256: `727772e1d9736dcf698ef452a02b8903e2a70010e322d15b68930c4ca05cb5ad`.
- Final battery: 12/12 green (`checks/after-final/`).
- Final focused tests: 34/34 pass (`checks/final-task-tests/`).
- Final census: 300/300 lessons materialized; production and rotations both `no_ambiguity_found` (`checks/lesson-census-1/`).
- No Racket source changed.
- No prior return was used as authority or implementation source.
## Current reviewer considerations

Source SHA-256: `727772e1d9736dcf698ef452a02b8903e2a70010e322d15b68930c4ca05cb5ad`.

# Decisions for `dfa9d0b2dd41`

## D1 — Keep the Racket authority unchanged and pin it

- **Prior choice:** generator `1.1.0` had no `RULE_HASH` pin and no executable mirror/contract tying its distribution to the selected rule.
- **New choice:** retain the existing Racket authority and pin `RULE_HASH = "76c3cefee423"`.
- **Reason:** direct canonical replay and rule smoke showed that the authority itself is correct; the defects were in generator distribution and contracts, not the transformation.
- **Probe/evidence:** `checks/after-final/` has green rule smoke, Racket lint, and authority sync; `checks/counterexample-bbox-area/racket.json` applies the authority to the retained witness.
- **Rejected alternative:** rewrite the Racket rule to match a simpler rectangle-only generator. That would change the task instead of teaching the existing one.
- **Limit:** the Python mirror is test/contract support; Racket remains label authority.

## D2 — Replace the rejection sampler with a constructive four-slot layout

- **Prior choice:** arbitrary polyominoes were placed by repeated random trials, with a risk of rejection and under-realized controls.
- **New choice:** every shape fits a `3×3` local slot; up to four slots are separated by one blank row/column inside a `7×7` footprint. A random global offset, slot permutation, object permutation, orientation, and palette permutation provide variation without rejection.
- **Reason:** every legal combination of `grid_h`, `grid_w`, and `n_objs` is now feasible and observable, including the minimum `8×10`/four-object case.
- **Probe/evidence:** exhaustive override stage green in `checks/after-final/`; focused boundary tests in `generators/dfa9d0b2dd41/tests/test_generator.py`.
- **Rejected alternative:** enlarge retry budgets. More retries would not make false axes meaningful or make every declared combination constructive.
- **Failure mode/limit:** this deliberately restricts generated components to shapes that fit `3×3`; the authority accepts broader shapes.

## D3 — Retire fake controls instead of preserving API appearance

- **Prior choice:** axes such as palette kind/size, position bias, distinct-color count, density, and textures were constants, aliases, narrowed by difficulty, or not reflected in pixels.
- **New choice:** expose only `grid_h` (`8..14`), `grid_w` (`10..18`), and `n_objs` (`2..4`), all strict integers and all exact in every band. Unknown/retired keys and coercive scalar values fail.
- **Reason:** an advertised axis should be falsifiable from returned pixels.
- **Probe/evidence:** baseline failures under `checks/before-override/`; final override stage green and task tests for every band/boundary.
- **Rejected alternative:** retain legacy names as ignored compatibility aliases. Silent acceptance is worse than a loud migration error because misspellings appear successful.
- **Limit:** palette and position still vary stochastically but are not caller-controlled.

## D4 — Make bounding-box-area the primary semantic rival

- **Observation:** all four labeled canonical pairs contain solid rectangles. For those inputs, occupied-cell count equals bounding-box area, so `bbox_area_sort` matches every canonical output.
- **New choice:** declare it in `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`, with an executable witness predicate.
- **Reason:** this is stronger and more task-specific than generic shortcuts such as sorting by color or position.
- **Probe/evidence:** canonical-fit assertions and exact witness regression in the task tests; retained case at `counterexamples/bbox_area_sort.json`.
- **Rejected alternative:** rely on random irregular polyominoes. Empirical occurrence is not a lesson-level guarantee.
- **Limit:** the declared-rival set is finite and cannot prove unique induction.

## D5 — Use one canonical-like anchor followed by two semantic witnesses

- **New schedule:** sample indices repeat `solid_rectangles, bbox_area_witness, bbox_area_witness`.
- **Reason:** with three demonstrations and one query, any four consecutive pairs contain at least two witnesses; holding out any one pair leaves at least one witness in the demonstrations. The solid slice preserves canonical morphology rather than replacing it entirely with adversarial shapes.
- **Probe/evidence:** exhaustive four-position rotation test and the 100-lessons-per-band census (`checks/lesson-census-1/`).
- **Rejected alternatives:**
  - alternating `solid,witness` leaves a three-pair lesson with only one witness, which can be removed by query rotation;
  - all-witness generation teaches the distinction but abandons canonical morphology;
  - ordered-only support would require declaring rotations unsupported.
- **Failure mode/limit:** the guarantee is against the declared bbox-area rival for this fixed lesson assembly, not every possible rival or arbitrary lesson size.

## D6 — Preserve canonical scale while making the rival disagree

- **Initial repair attempt:** witness components topped out at six cells. Defect lint correctly found that the distribution missed the canonical large-object band.
- **New choice:** solid anchors use sizes up to nine; witness profiles combine the five-cell L and six-cell rectangle with two- and/or nine-cell solids as object count permits.
- **Reason:** the decisive inversion remains local while canonical object scale is represented.
- **Probe/evidence:** failing intermediate receipt `checks/after-defect_lint-1/`, passing receipt `checks/after-defect_lint-2/`, and `test_default_component_scale_reaches_the_canonical_large_object_band`.
- **Rejected alternative:** add size only to a diagnostic override profile; ordinary defaults need the support.
- **Limit:** the generated maximum is nine cells although one canonical object reaches ten; the profile/defect gates accept the resulting scale support.

## D7 — Preserve exact canonical profiles in every band

- **New choice:** default draws cycle through `(10,12,3)`, `(11,13,3)`, `(9,14,3)`, and `(12,15,4)` object profiles (palette count is object count plus background).
- **Reason:** adversarial teaching should not drift away from the visible task family.
- **Probe/evidence:** final profile-floor and strict-distribution stages green; 20-draw profile floor is hit in easy, medium, and hard.
- **Rejected alternative:** use only broad random dimensions. That can have good envelope overlap while missing exact canonical anchors.

## D8 — Retain an exact source-bound counterexample

- **Choice:** store seed `31415`, sample index `1`, overrides `8×10/4 objects`, full input, authority output, rival output, source hash, and Racket replay metadata in `counterexamples/bbox_area_sort.json`.
- **Reason:** future maintainers should not have to reconstruct the strongest rival or trust a narrative claim.
- **Probe/evidence:** `test_retained_bbox_area_counterexample_matches_both_rules`; 34/34 final task tests pass.

## D9 — Treat controller interruptions as incomplete, not green

- **Observation:** the consolidated battery controller stopped between completed stages on two attempts. No failing stage was reported, but an interrupted aggregate is not a pass.
- **Choice:** retain the attempts and resume only with exact unchanged source/settings until the summary recorded all 12 stages green.
- **Evidence:** `checks/after-final/` contains checkpoint/resume history and the final all-green summary.

## Prior evidence use

No historical return or predecessor implementation was adopted as authority. The old selected generator, current canonical ledger, current Racket authority, and current packet checks were the evidence sources. The baseline source hash was `3e5b6aacbb5072cbb98cd068e0f37813a9b653bbc1447f0e7ae8723a6919313f`; the repaired source hash is `727772e1d9736dcf698ef452a02b8903e2a70010e322d15b68930c4ca05cb5ad`.
