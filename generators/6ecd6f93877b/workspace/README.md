# Workspace

The selected implementation is `../generator.py`; workspace tools are authoring aids, not label authority.

- `reference_probe.py` supplies an independent counting oracle, the two canonical-fitting rivals, and observable-axis helpers used by task-local tests.
- `qualify.py` is a fast pre-battery probe for exact overrides, deterministic replay, four-pair curriculum windows, all query rotations, shortcut witnesses, canonical shortcut fit, and output-shape drift.

From the packet root:

```bash
PYTHONPATH=repo/src:repo/shared/runtime:repo/generators/6ecd6f93877b/workspace \
  python3 repo/generators/6ecd6f93877b/workspace/qualify.py \
  --starts-per-band 20 --out checks/qualification.json
```

A clean probe is useful but not authoritative: the Racket-backed battery and lesson census remain required.
