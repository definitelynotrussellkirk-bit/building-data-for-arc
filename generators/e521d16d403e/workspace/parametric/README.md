# Native candidate for e521d16d403e

This task-local candidate extends the retained selection-metric prototype.
`adapter.py` is the native entrypoint; `native.py` owns construction, protected
Racket labeling and the single-query public projection. The production
generator and canonical authority are unchanged. Reviewer qualification is
separate from owner acceptance and training admission.

## Episode-fixed rule

`selection_rule` has exactly three values, held fixed over every pair:

| Value | Transformation |
|---|---|
| `occupied_cells` (default) | Find same-color four-connected components with width > 1 and a left-right symmetric raw bounding box; crop the largest by occupied-cell count. |
| `bbox_area` | Use the same eligibility test and crop the eligible component with largest bounding-box area. |
| `occupied_anchor_partner` | Select the occupied-cell winner, bind its color, then crop the unique other connected component with that color. |

The first two programs reuse `prototype.materialize_rule`; the default's full
source SHA-256 remains
`2119340b5d5b36791ddb26b8488686ab3e370eedcac4069d814914d8bc260cc6`.
The third program guards and replaces only the final crop binding. It transfers
the selected anchor's observed color to a different object-selection operation.
Replacing the occupied-cell anchor comparator with the area comparator chooses
the other anchor, changes the intermediate color and changes the returned
partner. This is the retained wrong-intermediate witness.

The composed rule falls back to the anchor if no partner exists and chooses the
first partner if several exist; the admitted grammar always has exactly one
partner for either main anchor. Tied
winners and missing/ambiguous partners are outside this candidate's sampler.

## Constructive grammar and counts

- Exact integer seeds: 0 through 2**63 - 1; booleans and floats are rejected.
- Independent counts: 2–6 demonstrations, 1–4 queries; ordinary usage is 3 + 4.
- Three eligible components: a dense anchor, a sparse anchor with a larger bbox,
  and a small decoy. The two main anchors have distinct asymmetric same-color
  partners. A width-one bar exercises the eligibility exclusion.
- The first two demos reverse eligible scan order, the anchors' tall/wide
  aspect roles, and partner location, size rank and proximity. A large
  UD-only symmetric partner supplies an ineligible
  distractor. No rejection loop or hidden-setting-dependent input stream is used.
- Query shapes are 14×18, 22×24, 30×30 and 26×30. The 30×30 case contains large
  objects in all quadrants and board-edge contacts; it is not empty padding.
- Palette, shape density, arm position, object placement, partner sizes and
  query role order vary deterministically with the seed. Components' raw bboxes
  remain separated, avoiding accidental bbox contamination or merging.

Demonstration and query streams are independent. Increasing queries from one
to four leaves all demonstrations and the first query unchanged. Increasing
demonstrations leaves the query stream unchanged. Every pair in an episode has
a distinct input; all settings share identical inputs for the same request.

## Model-visible projection

The native adapter returns full labeled pairs to the private controller.
`public_turn(episode, query_index)` uses the existing public serializer and
exposes only the demonstrations and one masked query. It emits no index, total,
future input, setting, seed, program or query answer. The first turn is identical
to the corresponding single-query episode. This is a projection helper, not a
training loop or turn controller.

`native.py --out ...` saves four-query episodes under `private/` and only their
first turns under `public/`. Public filenames are SHA-256 of the exact saved
canonical bytes. The legacy `prototype.py` writer now obeys the same byte rule;
its four authored fixtures remain available as earlier evidence.

## Focused reproduction

From the outer packet directory, use the interpreter that passes `python-check`:

```bash
python3 review.py run python3 -m pytest -q \
  generators/e521d16d403e/tests/test_native_parametric.py \
  generators/e521d16d403e/tests/test_parametric_prototype.py \
  generators/e521d16d403e/tests/test_parametric_public_names.py

python3 review.py run python3 \
  generators/e521d16d403e/workspace/parametric/native.py \
  --seed 17 --demos 3 --out ../checks/e521d16d403e/examples

python3 WORK/check_public_exports.py WORK/checks/e521d16d403e/examples/public \
  --demos 3 --queries 1

python3 review.py run python3 \
  generators/e521d16d403e/workspace/parametric/self_audit.py \
  --seeds 0 1 --demos 2 3 4 5 6 \
  --out ../checks/e521d16d403e/self-audit.json

python3 review.py run python3 -m arcpuzzles parametric qualify e521d16d403e \
  --out ../checks/e521d16d403e/qualification --summary
```

Use new output paths for reruns. Before qualification, refresh the task-local
manifest using the existing `parametric manifest` command with exact guarded
replacement; see `docs/parametric-promotion.md`. The native owner must qualify
and accept the exact integrated sources after intake. No supplied source or
evidence file grants acceptance on its own.

`self_audit.py` is a reusable bounded teaching probe. It identifies rivals that
fit every visible demo but disagree on a query, and retains the failing lesson.
Selected labels, native alternative programs and the wrong-anchor rival execute
in protected Racket. Named Python object heuristics are diagnostic mirrors and
are labeled accordingly. A pass is limited to the declared rivals and samples;
it is not universal identifiability or measured learning benefit.
