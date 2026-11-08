# Minimum-visible-port prototype

This task-local prototype keeps the original `c4f6a0585dbf` reasoning pattern and varies one guard once per complete episode:

| `min_visible_ports` | Meaning | Authority |
| --- | --- | --- |
| `2` | Stamp a transformed template when at least two in-bounds port markers align. | Exact canonical Racket bytes; original default. |
| `3` | Require all three source ports to remain in bounds and align. | Canonical Racket with only the literal guard `2` changed to `3`. |

Each episode contains three labeled demonstrations and four distinct answer-masked queries. Seeds `2k` and `2k+1` share the same seven inputs and choose settings `2` and `3`, respectively. Every retained input includes a complete three-port trigger and a boundary-clipped two-visible-port trigger, so the two lawful settings differ on every pair. The selected setting is fixed before any example is generated.

Run from the packet root:

```bash
python3 review.py run python3 \
  generators/c4f6a0585dbf/workspace/parametric/prototype.py \
  --seed 0 \
  --out ../checks/parametric/c4f6a0585dbf-min-visible-ports-v2
```

The writer creates private Racket programs and complete labels separately from public challenges. Public files contain only demonstrations and query inputs; their bytes and full content IDs come from `reviewer_support.public_challenge_bytes` and `public_challenge_id`. Existing output directories are never overwritten.

This is a bounded authoring prototype, not a canonical-rule change, production API, approval, or training-admission decision. Its retained evidence covers two paired episodes, the sole opposite-setting rival, and all ten canonical labels.
