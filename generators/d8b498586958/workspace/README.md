# Workspace

The selected implementation is `../generator.py`. Workspace probes are review
evidence and are never selected as production code.

## `lesson_window_probe.py`

Audits the actual declared `LESSON_COMPETITORS` and `CANONICAL_SHORTCUTS` over
all requested schedule starts. It reports two populations separately:

- **production windows:** four consecutive demonstrations, then the next pair as
  query. Every start must pass.
- **arbitrary query rotations:** every member of the same five-pair window is
  moved into the query position. This stronger population is outside the current
  assembly contract and intentionally records the branch-withholding limitation.

From `repo/`:

```bash
PYTHONPATH=shared/runtime python3 \
  generators/d8b498586958/workspace/lesson_window_probe.py \
  --seed-count 32 --start-count 16 \
  --out ../checks/lesson-window-probe.json
```

The JSON binds results to the exact generator SHA-256, enumerates the rival
names dynamically, and keeps concrete failing rotation examples.
