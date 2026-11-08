# Workspace

The selected implementation is `../generator.py`. Workspace probes are review tools only and are never selected automatically.

## Semantic census

`semantic_census.py` is a deterministic, source-bound curriculum audit. It imports the selected generator from an explicit prepared runtime and reads the generator's own `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, schedule, and example count. It checks every cyclic lesson start, visible-demo rival refutation, canonical shortcut fit, generated disagreements, uniqueness, invalid inputs, witness counts, and source hashes.

Run it against a prepared runtime rather than the source checkout:

```bash
ARCP_RUNTIME_ROOT=/absolute/path/to/prepared-runtime \
python3 workspace/semantic_census.py \
  --runtime-root /absolute/path/to/prepared-runtime \
  --lessons-per-band 100 \
  --out /tmp/3ae696dbdba9-semantic-census.json
```

The tool labels examples with the task-local Python mirror. Pair its results with the official rule-smoke and authority checks; the census is not a substitute for Racket execution parity. Its regression test is `test_semantic_census.py`.
