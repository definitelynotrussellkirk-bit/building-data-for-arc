# Workspace

The selected implementation is `../generator.py`; workspace drafts are never automatically selected.

- `baseline_generator_v3.py`: immutable copy of the reviewed baseline for comparison.
- `probe_curriculum.py`: fast source-bound authoring probe. It reads live generator declarations, models consecutive exact-input de-duplication, checks two-of-each profile balance, and holds out every accepted pair once. It uses the Python mirror and therefore does **not** replace the Racket-backed census.

Run from the repository root:

```bash
PYTHONPATH=shared/runtime python3 generators/d5af7195f6da/workspace/probe_curriculum.py \
  --per-band 100 --out ../checks/curriculum-probe.json
```

A nonzero exit means generation, balance, or rotation-identifiability failure. Final authority verification still requires `run_with_racket.py ... lesson-census`.
