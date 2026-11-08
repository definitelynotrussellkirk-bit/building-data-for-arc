# Workspace tools for eb92fce9b549

The selected implementation is `../generator.py`. Nothing in this directory is auto-selected by the catalog.

## Files

- `history/generator-v2.2.0-original.py` — immutable review copy of the imported generator used for before/after regression reproduction.
- `reference_probe.py` — independent canonical loader, 4-connected component parser, bounding-box measurements, intended/rival output oracles, and observable-axis decoder.
- `semantic_probe.py` — source-bound long-run lesson census using the actual shared runner and Racket bridge. It reads the generator's declared semantic rival/witness hooks rather than maintaining a separate rival-name list.

## Re-run the long census

From `repo/`, with the packet's Racket runtime selected by the wrapper:

```bash
cd ..
python3 run_with_racket.py \
  python3 generators/eb92fce9b549/workspace/semantic_probe.py \
  --per-band 100 \
  --out ../checks/semantic-probe-final.json
```

The report records generator and probe SHA-256 values, the exact seed formula and sample-index stride, actual lesson assembly, canonical shortcut fit, uniqueness, profiles, strict failures, witness/rival disagreements, and per-band denominators. It deliberately limits its claim to the sampled domain and declared rival.

## Run task-local tests against another draft

```bash
cd repo
GENERATOR_UNDER_TEST=/absolute/path/to/generator.py \
PYTHONPATH=shared/runtime \
pytest -q generators/eb92fce9b549/tests/test_generator_review.py
```
