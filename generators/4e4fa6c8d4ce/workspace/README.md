# Review workspace

`analyze_generator.py` is the replayable distribution and shortcut probe added by
review `review-9dff8738d2938418`.

From the packet root:

```bash
python3 run_with_racket.py python3 \
  generators/4e4fa6c8d4ce/workspace/analyze_generator.py \
  --seed 8500 --sample-index 2 --difficulty medium --census 80 \
  --out ../checks/shortcut_witness.json
```

It loads the selected canonical Racket rule, generates one exact input, compares
Racket against the Python mirror, evaluates the canonical `drop_shape_color`
shortcut, records hashes/axes/witnesses, and optionally produces a small census.
The report exits nonzero if Racket parity or shortcut separation fails.
