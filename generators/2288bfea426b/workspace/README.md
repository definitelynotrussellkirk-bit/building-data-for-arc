# Workspace

- `generator-v2.0.1-baseline.py` is the immutable pre-repair source retained for comparison.
- `reference_probe.py` is an independent Python geometry oracle and reproducible distribution audit. It is supplementary evidence, not label authority.

From `repo/`, run:

```bash
PYTHONPATH=shared/runtime python3 generators/2288bfea426b/workspace/reference_probe.py \
  --count 250 --racket --out ../checks/2288bfea426b-reference-probe.json
```

`--racket` is fail-closed: it executes the canonical Racket rule and never
silently substitutes the Python oracle.
