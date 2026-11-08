# Workspace

`reference_probe.py` is the reusable task-local audit tool for generator `4a279b104523`. It independently extracts canonical pairs, implements the reflection geometry, measures observable axes and declared rival disagreements, checks determinism, and can compare sampled outputs with the real Racket authority.

From the packet root:

```sh
python3 run_with_racket.py python3 \
  generators/4a279b104523/workspace/reference_probe.py \
  --count 250 --racket --out ../checks/final/reference_probe.json
```

The selected implementation is `../generator.py`; workspace files are probes and handoff aids, never automatically selected as production code.
