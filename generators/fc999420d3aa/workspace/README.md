# Review workspace

The selected implementation is `../generator.py`; workspace files are diagnostic
only and are never automatically selected.

Run the fast source-local probe from the packet root:

```bash
python3 run_with_racket.py python3 generators/fc999420d3aa/workspace/review_probe.py \
  --out ../checks/fc999420d3aa-review-probe.json
```

The probe checks canonical-shortcut fit, the historical duplicate-color seed,
all exact-axis boundary corners in every band, and cyclic three-demo/query
rotations. The authoritative large check remains `arcpuzzles lesson-census`,
which labels with Racket rather than the Python mirror.
