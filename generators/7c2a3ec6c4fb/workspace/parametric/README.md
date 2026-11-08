# Native parametric family: 7c2a3ec6c4fb

`as_found` is the selected canonical Racket source byte-for-byte.
`marker_to_top_left` performs the same exact duplicate-crop census, selects the
one crop occurring once, derives the only singleton-colored corner inside that
selected crop, and flips the crop along exactly the axes needed to move the
marker to the upper-left.

The sampler is independent of the private setting, supports 3–6 demonstrations
and 1–4 prefix-stable queries, and uses full nonzero objects with identical
shape and color histograms across classes. The first three demonstrations put
the marker at top-right, bottom-left, and bottom-right, separating the two
settings and the retained fixed-axis shortcut bank. Query four is a dense
30×30 scene containing nine 6×6 objects and reaching every boundary.

Reusable authoring checks from the packet root:

```bash
python3 review.py run python3 generators/7c2a3ec6c4fb/workspace/parametric/audit.py \
  --seeds 20 \
  --out generators/7c2a3ec6c4fb/workspace/parametric/evidence/current/self_audit.json
python3 review.py run python3 -m arcpuzzles parametric qualify 7c2a3ec6c4fb \
  --out ../checks/7c2a3ec6c4fb/qualification --summary
```
