# Source-bound review workspace

`review_probe.py` is a reusable companion for the selected generator. It reads
`CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS` directly from `../generator.py`,
checks every declared shortcut on all canonical pairs, checks every query
rotation for every cyclic start of the two-step schedule, and exercises exact
joint override boundaries in every difficulty band.

From `repo/`:

```bash
python3 generators/0d0f5035a157/workspace/review_probe.py \
  --seeds-per-band 16 \
  --out ../checks/review-probe.json
```

The result is finite evidence against the declared rivals, not a universal
proof that no other rival rule exists.
