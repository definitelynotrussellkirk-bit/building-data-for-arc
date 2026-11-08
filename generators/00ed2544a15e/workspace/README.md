# Workspace

The selected implementation is `../generator.py`. Workspace tools are retained
authoring aids and are never automatically selected.

## `curriculum_probe.py`

A portable, source-bound audit that reads the generator's live
`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and schedule declarations. It:

- checks the Python mirror against all canonical pairs;
- proves each declared canonical shortcut actually fits those pairs;
- exhausts every cyclic schedule start and every query rotation;
- checks all 300 legal joint `grid_h`/`grid_w`/`profile`/difficulty combinations;
- records exact generated shortcut counterexamples and same-color component counts;
- checks deterministic replay over a configurable sample.

From the packet root:

```sh
python3 run_with_racket.py python3 \
  generators/00ed2544a15e/workspace/curriculum_probe.py \
  --sampled-draws-per-band 25 \
  --out ../checks/curriculum-probe.json
```

This is a fast Python-side authoring probe. The Racket-backed battery and shared
lesson census remain the authority and production-sampler evidence.
