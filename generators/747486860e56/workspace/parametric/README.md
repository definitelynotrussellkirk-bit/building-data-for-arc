# Proposed triangle-leg parameter for `747486860e56`

This is a **proposed, unapproved** task-local prototype. It does not change the
production generator or canonical rule.

The hidden episode parameter `triangle_leg_mode` has two values:

- `residual_minus_one` — original/default: triangle leg is `K - 1`.
- `residual_count` — proposed alternative: triangle leg is `K`.

`K` is the number of nonzero residual cells after the uniquely largest
multicolor 8-connected object is selected. Object selection, voting, row-major
tie breaking, corner orientation, erasure, and paint order remain unchanged.
The alternative requires `K <= min(height, width)`; the canonical setting only
requires `K - 1 <= min(height, width)`.

From the outer extraction directory, create fresh executable evidence with:

```bash
python3 review.py run python3 generators/747486860e56/workspace/parametric/prototype.py \
  --seeds 0 1 --out ../checks/parametric/triangle-leg-v1
```

Run the focused tests with:

```bash
python3 review.py run python3 -m pytest \
  generators/747486860e56/tests/test_parametric_triangle_leg.py -q
```

Public episode files contain only demonstration inputs/outputs and a query
input. Private files retain the parameter, exact Racket source and query answer.
All labels are produced by the bundled Racket bridge, never by a Python mirror.
