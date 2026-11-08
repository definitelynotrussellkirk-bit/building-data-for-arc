# Workspace

The selected implementation is `../generator.py`.

## `distribution_probe.py`

This reusable task-local probe exhausts the advertised joint override matrix,
checks `self_check` and `observe_overrides`, measures palette/dimension/origin
support, and holds out every pair in consecutive five-pair lessons against the
generator's own `LESSON_COMPETITORS` contract. It can load an earlier source
file with `--generator` for source-hash-bound before/after comparisons.

Example from the packet root:

```bash
PYTHONPATH=repo/src:repo/shared/runtime \
  python3 repo/generators/73906110dd67/workspace/distribution_probe.py \
  --out checks/distribution/after.json
```

The probe uses the independent Python mirror for high-volume diagnostics. It
does not replace Racket authority checks, the official battery, or the shared
source-bound lesson census.
