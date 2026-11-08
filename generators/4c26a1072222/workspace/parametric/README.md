# Forward/inverse application prototype

This task-local prototype keeps the original per-band reasoning structure:
infer the authority-selected D4 transform and functional A→B color map, then
apply the map to transformed C. One hidden value is chosen once per episode:

- `forward` — apply the inferred transform to C; this is the registered
  canonical rule and its Racket source is returned byte-for-byte.
- `inverse` — apply the inverse transform to C while retaining the same learned
  color map. Only clockwise and counterclockwise quarter turns swap; the other
  six D4 operations are self-inverse.

Each episode contains four demonstrations and four distinct queries. Input
sampling is identical across settings for a fixed seed, and every retained input
contains an observable quarter-turn distinction. The public export includes only
demonstrations and query inputs; seed, setting, programs, sampling receipts, and
query labels remain private. The verifier writes the canonical visible challenge
bytes directly, so the SHA-256 of each emitted `public.json` is exactly its public
ID. Batch manifest rows are sorted by that opaque ID, and duplicate visible
payloads fail closed. This is proposed evidence, not production wiring or
canonical approval.

From the packet root, run exact Python/Racket verification for both settings:

```bash
python review.py run python3 \
  generators/4c26a1072222/workspace/parametric/verify.py \
  --all-settings \
  --output-dir ../checks/parametric \
  --overwrite
```

From `WORK/repo/`, run the focused unit tests:

```bash
PYTHONPATH=shared/runtime:src python -m pytest -q \
  generators/4c26a1072222/tests/test_parametric_application_direction.py
```

Run the bounded sampler/export adversarial probe from `WORK/repo/`:

```bash
PYTHONPATH=shared/runtime:src python \
  generators/4c26a1072222/workspace/parametric/adversarial_probe.py \
  --out ../checks/parametric-adversarial.json
```
