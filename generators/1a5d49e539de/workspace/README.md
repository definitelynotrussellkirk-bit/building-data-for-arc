# Workspace

`review_probe.py` is the retained source-bound distribution and lesson probe for
this generator. It discovers rivals from the live generator declarations rather
than copying a name list.

Run from the packet root:

```bash
python3 run_with_racket.py python3 \
  generators/1a5d49e539de/workspace/review_probe.py \
  --per-band 100 --out ../checks/review-probe.json
```

The report binds itself to the generator SHA-256 and records per-band input and
output uniqueness, dimensions, colours, target scan indices, target size ranks,
maximum object size, strict-domain acceptance, complete three-demo lesson rival
refutation, and exhaustive `grid_size` x `color` axis corners.

The selected implementation remains `../generator.py`; workspace drafts are
never automatically selected.
