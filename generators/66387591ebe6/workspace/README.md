# Workspace

The selected implementation is `../generator.py`.

- `generator_v1_3_0_baseline.py` is the immutable selected baseline copied before repair for local comparison.
- `lesson_probe.py` is a source-bound lesson census. It assembles consecutive-index lessons using the shared semantic gate's stride of 11, iterates the generator's actual witness/competitor declarations, records uniqueness and per-band coverage, and separately audits the exact key-1 identity override.

Run the final 100-lessons-per-band census from the packet repository directory:

```bash
python3 generators/66387591ebe6/workspace/lesson_probe.py \
  --repo . \
  --generator generators/66387591ebe6/generator.py \
  --lessons-per-band 100 \
  --seed-base 663875910 \
  --out ../checks/lesson-probe-100-per-band-v2.json
```

The high-volume probe uses `rule_mirror` for speed. Independent Racket-backed `rule_smoke`, `semantic_gate`, and `authority_sync` results are required corroboration.
