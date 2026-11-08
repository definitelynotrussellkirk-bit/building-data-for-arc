# `a7d4df2828a0` native placement family

This task-local family preserves the selected canonical rule exactly and adds one
nearby episode-fixed placement rule over the same inputs.

| `placement` | Meaning |
|---|---|
| `bbox_top_left` | Canonical/default: transform the motif according to the control and place the normalized result at the input motif bounding-box origin. |
| `preserve_first_cell` | Apply the same transform, track the row-major first motif cell through it, and translate the result so that transformed cell remains at its original absolute coordinate. |

The input sampler is independent of the private setting. It supports 2–6
demonstrations and 1–4 queries with stable prefixes. Every maximal episode has
four distinct queries; the fourth is a substantive 30×30 boundary/stress case.
`public_turn` exposes one query input at a time and omits settings, programs,
answers, future queries, and total-query hints.

The sequential dependency is real: the transform moves an input-dependent pivot
in Step A, and Step B cannot choose the translation until it knows that derived
transformed coordinate. `self_audit.py` checks declared rivals and replays a
wrong-intermediate counterfactual through protected Racket.

From the packet outer directory:

```bash
python3 review.py run python3 generators/a7d4df2828a0/workspace/parametric/self_audit.py \
  --out generators/a7d4df2828a0/workspace/parametric/evidence/replay-new
python3 review.py run python3 -m arcpuzzles parametric qualify a7d4df2828a0 \
  --seed 0 --seed 17 --demos 2 --queries 4 \
  --out ../checks/a7d4df2828a0/qualification-new --summary
python3 review.py task-tests a7d4df2828a0 --phase after \
  --out ../checks/a7d4df2828a0-tests-new
```

These are reviewer artifacts only. Owner exact-source acceptance and any training
admission remain separate.
