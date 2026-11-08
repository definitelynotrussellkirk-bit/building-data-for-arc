# e12f9a14 parametric workspace

Settings: `collision_rule=vector_sum|stop`. The canonical copy is
`canonical.rkt`; `adapter.py` returns that exact text for the default.

Focused checks from the repository root:

```bash
PYTHONPATH=shared/runtime:src pytest -q generators/public_eval_e12f9a14/tests
python3 generators/public_eval_e12f9a14/workspace/parametric/collision_trace.py \
  --seed 17 --sample-index 2 --out /tmp/e12-trace.json
```

The trace records launcher gaps, geometric merge points in doubled coordinates,
unequal travel distances, member identities, and resulting courses.
