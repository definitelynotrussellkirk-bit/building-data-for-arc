# Task-local review tools — b8cd4b7fd7a4

`reference_probe.py` is an independent geometry oracle and repeatable sampler
audit. It does not import generator helpers when computing expected outputs or
rivals. Racket mode is required for authority qualification and never falls back
to Python.

From the repository root:

```bash
PYTHONPATH=shared/runtime:src python3 -B -m pytest -q \
  generators/b8cd4b7fd7a4/tests
PYTHONPATH=shared/runtime:src python3 -B \
  generators/b8cd4b7fd7a4/workspace/reference_probe.py \
  --count 1000 --racket --out ../checks/reference-probe.json
```

The audit records canonical oracle matches, deterministic replay, strict/self
validation, shapes, orientations, endpoint colors, distinct inputs, and four
executable rival disagreements per difficulty band. These finite checks are
supporting evidence, not training approval or a universal proof.
