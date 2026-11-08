# Workspace for `cfd0943c5b14`

The selected implementation is `../generator.py`; workspace files are reviewer tools and are not automatically selected.

## `reference_probe.py`

Small independent helpers for interpreting seed cells and computing the intended clipped diagonal-X union. Tests use this instead of calling the generator's `rule_mirror`, so layout code and expected-output code are not the same implementation.

## `contract_probe.py`

Reusable source-bound distribution and lesson probe. It samples every difficulty band, verifies `self_check`, compares generator behavior with the independent stencil oracle, checks declared rivals, and exhausts all five held-out query rotations across a configurable number of cyclic starts.

Final command used from `repo/`:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/shared/runtime:$PWD" \
  python3 generators/cfd0943c5b14/workspace/contract_probe.py \
  --draws-per-band 100 --schedule-starts 100 \
  --out ../checks/contract-probe-v2.json
```

Final result: 300 draws, 289 distinct inputs, 1,500 rotations, zero ambiguities, zero errors. The earlier failing `checks/contract-probe.json` is intentionally retained because it exposed causally redundant cyan witnesses.
