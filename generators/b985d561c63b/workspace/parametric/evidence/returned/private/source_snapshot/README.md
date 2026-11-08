# Proposed `stamp_anchor` episode rule

Status: **proposed and unapproved**. This directory does not change the fixed-rule production generator.

The prototype selects exactly one hidden value per complete episode:

- `top_left` — the byte-exact canonical Racket rule and default behavior.
- `bottom_right` — the same full-bounding-box stamp, including source zeros, aligned to the target rectangle's lower-right corner.

Each episode contains three labeled demonstrations and one masked query. Inputs are produced by the selected `b985d561c63b` sampler independently of the hidden value, with a dense source and exactly one row and one column of gray surplus. Those controls force the two anchors to disagree while preserving the same source/target roles and stamping concept. Both retained labels and rival predictions are executed through `RacketBridge`; an independent Python mirror is only a cross-check.

Run from the review repository through the bundled wrapper:

```bash
python3 review.py run python3 generators/b985d561c63b/workspace/parametric/prototype.py \
  --seeds 0 1 --out ../checks/parametric/stamp-anchor-v1
```

The `public/` files expose labeled demonstrations and query inputs only. Exact rule text, hidden parameters, query labels, rival predictions, canonical replay, and source snapshots remain under `private/`.
