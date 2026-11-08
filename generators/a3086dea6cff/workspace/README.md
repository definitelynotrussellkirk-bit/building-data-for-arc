# Workspace

The selected implementation is `../generator.py`. Workspace files are review
artifacts and are never automatically selected.

- `generator-before.py` is the exact imported generator used for the frozen
  before census.
- `audit_curriculum.py` is an independent source-bound probe. It implements the
  intended rule and five rivals without importing the selected generator's
  semantic hooks, then audits individual scenes, sliding three-example lessons,
  canonical-profile support, and exact generated counterexamples.

Example from the packet repository root:

```bash
PYTHONPATH=src:shared/runtime python3 \
  generators/a3086dea6cff/workspace/audit_curriculum.py \
  --generator generators/a3086dea6cff/generator.py \
  --seeds 20 --starts 9 \
  --json-out ../checks/a3086dea6cff_curriculum_after.json
```
