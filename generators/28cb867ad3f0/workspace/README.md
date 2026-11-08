# Workspace

The selected implementation is `../generator.py`. Workspace probes are reviewer tools and are never selected automatically.

## Shortcut and schedule probe

`shortcut_probe.py` uses only the public `reviewer_support` loader and the generator's own current declarations. It verifies canonical fit for every `CANONICAL_SHORTCUTS` entry, counts generated disagreements for every `SEMANTIC_RIVALS` entry, and exhausts every declared schedule residue and query rotation.

From `WORK/repo/`:

```bash
PYTHONPATH=src:shared/runtime python3 generators/28cb867ad3f0/workspace/shortcut_probe.py \
  --seed 0 --per-band 36 --out ../checks/final-shortcut-probe.json
```

The retained final report is source-bound to generator SHA-256 `402c0cb6bc5f73f1cbd70a739f4792dd4e1f398c27e239b383a7a9cfc4977324`.
