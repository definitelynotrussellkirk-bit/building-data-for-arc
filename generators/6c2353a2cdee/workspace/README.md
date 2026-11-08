# Workspace

The selected implementation is `../generator.py`; workspace files are retained evidence/tools and are never automatically selected.

- `generator_before_review.py` — exact imported generator (`5e623a…`) used as the before source.
- `distribution_probe.py` — reusable task-linked canonical/before/after analyzer. It records source hashes, deterministic seed policy, morphology, code grammar, output-count visibility, self-check acceptance, uniqueness, and per-band support.
- `distribution_before_after.json` — final report for 40 samples per band from each source plus all canonical inputs.

Reproduce from the repository root:

```bash
PYTHONPATH=shared/runtime python3 generators/6c2353a2cdee/workspace/distribution_probe.py \
  --before generators/6c2353a2cdee/workspace/generator_before_review.py \
  --after generators/6c2353a2cdee/generator.py \
  --canonical shared/data/canonical/puzzles.jsonl \
  --samples-per-band 40 --seed-base 7331 \
  --out generators/6c2353a2cdee/workspace/distribution_before_after.json
```
