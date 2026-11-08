# Crossing-ray payload parametric family

## Settings

- `finish=canonical`: exact canonical program bytes.
- `finish=first_hit_payload`: run the canonical expansion; scan the resulting yellow cells in row-major order; choose the first adjacent payload color in `{7,9}`; recolor every remaining cell of that color to `8`.

`skip_a.rkt` is the causal ablation: it attempts the selector/recolor stage on the original input, where no yellow ray exists.

## Files

- `adapter.py`: native `program(settings)` and `generate(seed, settings, demos, queries)` API plus authored certificate checks.
- `prototype.py`: deterministic matched-input sampler, Python reference semantics, scene facts, and the semantic rival bank.
- `promotion.json`: parameter space and count contract.
- `canonical.rkt`, `first_hit_payload.rkt`, `skip_a.rkt`: exact Racket programs.
- `adversarial_probe.py`: future-agent audit for prefixes, matched inputs, minimum lessons, rivals, crossed controls, malformed certificates, dimensions, boundaries, and optional protected-Racket evidence binding.
- `evidence/manifest.json`: source-bound author inventory.

## Re-run the focused checks

From `WORK/repo`:

```bash
PYTHONPATH=src:shared/runtime pytest -q \
  generators/4d0f228177b0/tests/test_base_portable.py \
  generators/4d0f228177b0/tests/test_parametric_4d0f228177b0.py

python3 generators/4d0f228177b0/workspace/parametric/adversarial_probe.py \
  --seeds 64 \
  --racket-execution generators/4d0f228177b0/workspace/parametric/evidence/racket_execution.json \
  --out /tmp/4d0f228177b0-adversarial.json
```

The probe is finite evidence, not a universal proof of identifiability.
