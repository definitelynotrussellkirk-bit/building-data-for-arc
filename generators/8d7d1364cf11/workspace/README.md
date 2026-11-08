# Review workspace: 8d7d1364cf11

`reference_probe.py` is a portable, independent audit for the repaired generator.
It reimplements component discovery and stamping without importing generator
helpers, checks canonical pairs, samples every difficulty band, probes declared
rivals, and can cross-check up to 64 inputs through the public canonical Racket
`arcpuzzles apply` command.

From the extracted packet root:

```bash
python3 review.py run python3 generators/8d7d1364cf11/workspace/reference_probe.py \
  --count 100 --axis-matrix --racket \
  --out ../checks/reference-probe.json
```

The axis matrix is the full product of shape count, copies, decoy count, all six
shape families, shared/distinct body palettes, four difficulty bands, and
min/mid/max grid dimensions: 5,184 cases. Python output is supplementary; only
the `--racket` path checks labels against the selected canonical authority.
