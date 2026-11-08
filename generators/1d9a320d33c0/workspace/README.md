# Workspace and reusable probes

The selected implementation is `../generator.py`. The primary reusable audit is the task-local pytest suite:

```bash
cd repo
PYTHONPATH=shared/runtime pytest -q generators/1d9a320d33c0/tests/test_generator_1d9a320d33c0.py
```

It independently checks all canonical pairs, the pinned rule hash, every cross-product of the three public axis boundaries in every difficulty band, curriculum profile/orientation/spacing coverage, malformed-input rejection, draw provenance, semantic rivals, determinism, fresh return values, and isolation from Python's global RNG.

The repository's semantic gate additionally executes the named rivals against the canonical Racket authority. The review return retains a 500-draw before/after branch census and a 160-draw-per-band curriculum census under `checks/`.
