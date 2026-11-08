# Workspace

The selected implementation is `../generator.py`; workspace tools are diagnostic
and are never selected automatically.

`probe_curriculum.py` independently enumerates all 512 joint endpoint
combinations of the seven public controls and every held-out query rotation for
a configurable number of cyclic schedule starts. From the repository root:

```bash
PYTHONPATH=shared/runtime:src python3 \
  generators/2c8fab02e3fe/workspace/probe_curriculum.py \
  --starts 64 --out ../checks/curriculum-probe-v22.json
```

The retained final-source run covers 192 windows and 768 query rotations. The
probe discovers rivals from the generator's own declarations, verifies that
each claimed canonical shortcut fits every canonical pair, and binds its report
to the generator SHA-256. The focused test suite also checks the pinned
canonical-profile census and cross-seed role deconfounding so schedule changes
cannot silently restore the intermediate side/color proxy.
