# Native panel-count and fixed-threshold family

Status: native reviewer qualification is required; owner acceptance remains separate.
The production generator and selected canonical program are unchanged.

`adapter.py` is the native entrypoint. `native.py` reuses the retained prototype's
fixed-threshold rule materializer and adds a composed rule. `prototype.py` is
retained legacy authoring evidence; its old three-demo/single-query gallery is
not the native teaching API. Use the commands below for new lessons.

## Rules and admitted input grammar

`axis_tolerance` has four values: `0`, `1`, `2`, and `"target_panel_count"`.
The default `1` returns the exact canonical Racket string byte for byte.
Fixed values move one signed cell on each axis whose target distance exceeds
the tolerance. Restore the old marker to5 and recolor the6 target as9.

The composed setting first finds the separator-defined panel containing6,
then counts its cells colored1,2,3,4,8, then uses that count as the movement
threshold. The panels and distractors therefore affect the action. No private
setting is encoded in an input. All settings receive identical inputs for the
same seed/count request. The sampled target-panel count is0,1,or2; other panels
may contain substantially more clutter. Counts mean cells, including repeated
colors, not distinct colors or connected components.

Inputs preserve the original full-zero separators, modal7 background, central
3×3 ring, unique9 and6, and sparse-to-dense distractor grammar. The separate
native family covers8×8 through30×30, beyond the production sampler's28 limit.
Large queries populate at least eight panels; separators, distractors and targets
reach boundaries. The full retained labels are executed in protected Racket.

## Teaching and counts

Support4–6 demonstrations and exactly4 distinct novel queries. Four demos are
the supported minimum: three left fixed-direction and never-move-an-axis
shortcuts. The four constructive roles, before a common dihedral transform, are:

| Role | Target delta | Selected-panel distractors |
|---|---|---|
| A | (1,4) |0|
| B | (2,-4) |2 (connected same-color pair)|
| C | (4,1) |2 (separated same-color pair)|
| D | (-4,2) |1|

These roles teach both axis thresholds, positive/negative movement, independent
axis gating, and counts0/1/2. Two same-color cells distinguish cell count from
color count and connected-group count. Randomized layouts and clutter vary across seeds. Input RNGs are
separate from settings and requested counts, so changing demonstration count
does not change the four queries. Every example within an episode is unique.

The bounded review fits declared settings plus independent-axis, fixed-direction,
global-dead-zone, panel-direction and panel-count shortcuts to demonstrations
only. Survivors are allowed only if they agree on all four queries. This is
finite evidence, not universal uniqueness.

## Run and reproduce

From the packet's outer folder, with its selected Python environment:

```sh
WORK/.venv/bin/python review.py run python3 -m pytest \
  generators/a85f5274d2ae/tests/test_native_parametric.py \
  generators/a85f5274d2ae/tests/test_native_exports.py \
  generators/a85f5274d2ae/tests/test_native_component_counts.py -q
WORK/.venv/bin/python review.py run python3 \
  generators/a85f5274d2ae/workspace/parametric/verify_native.py \
  --seed 0 --seed 17 --out ../checks/a85f5274d2ae/fresh-native-audit
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  a85f5274d2ae --seed 0 --seed 17 --demos 4 --queries 4 \
  --out ../checks/a85f5274d2ae/fresh-qualification --summary
```

Use a fresh output directory each time. The native manifest must describe current
source before qualification. Owner integration must freshly qualify and accept
its exact live bytes; this return does not self-approve variants or training data.

## Public/private boundary

The verifier retains one complete controller-side episode per setting and seed, each with4 demos and4 queries. The retained final audit uses seeds0,17,24. It also executes the6-demo boundary.
`private/` holds programs, settings, query labels and the turn-to-episode map.
`public/` contains only opaque content-hashed one-query challenge files.
`native.public_turn(episode,index)` exposes the same demonstrations and one
unlabeled query, with no future inputs, ordinal or total-count hints. Its first
turn equals the projection of a single-query episode. No turn controller or
training loop is added. Negative tests reject hidden fields, answers, extra
queries, a wrong query, and boolean-valued grid cells.
