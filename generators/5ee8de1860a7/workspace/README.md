# Workspace

The selected implementation is `../generator.py`; files here are diagnostics,
not automatically selected production code.

## `check_rotation_windows.py`

Enumerates overlapping four-pair default lessons for all three difficulty bands,
holds out each of the four pairs as query, and independently checks the three
documented teaching rivals (fixed color, fixed dimensions, center-only). It
also compares those findings with the generator's `lesson_identifiable` hook.

From `repo/generators/5ee8de1860a7/`:

```bash
python3 workspace/check_rotation_windows.py \
  --seeds 64 --windows 201 \
  --json-out ../../../checks/rotation-windows-after.json
```

The default run covers 38,592 overlapping windows and 154,368 query rotations.
It is a finite task-local census, not a proof against undeclared rivals.
