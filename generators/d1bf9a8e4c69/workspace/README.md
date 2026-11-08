# Workspace for d1bf9a8e4c69

The selected implementation is `../generator.py`. Workspace files are supporting evidence/tools and are never selected automatically.

## Files

- `baseline_generator.py` — immutable copy of the imported source, SHA-256 `ada66b645985e011eef3f969e15029905e2d9bff2a51e4c274ca266bfba0194f`.
- `distribution_probe.py` — source-bound census and teaching-contract probe. It loads the selected generator, reads its actual `AXES`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, schedule, and canonical pairs, then reports distribution support, shortcut counterexamples, all cyclic lesson windows, and the repository's pinned profile census.

Run from repository root:

```bash
PYTHONPATH=shared/runtime python3 generators/d1bf9a8e4c69/workspace/distribution_probe.py \
  --samples-per-band 24 \
  --lesson-starts 4 \
  --out ../checks/final_distribution_probe.json
```

The retained final report is `checks/final_distribution_probe.json` at packet root. It is bound to generator SHA-256 `458e1558ab9ada63796e1b5ab6a9601f4bd28094c0687140aedf17390105c86b`.
