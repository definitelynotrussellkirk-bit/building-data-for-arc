# Workspace

The selected implementation is `../generator.py`. Workspace code is review-only and is not selected as the production generator.

- `lesson_probe.py` independently checks every cyclic start and every query rotation of the six-slot teaching schedule, verifies declared canonical shortcuts against the three public pairs, reports tetromino-pair pool sizes, and samples each difficulty band for diversity and witness frequency.

Example from a repository root:

```bash
PYTHONPATH=src python3 generators/95f849a2fe0f/workspace/lesson_probe.py \
  --per-band 100 --out ../checks/schedule-probe.json
```

The probe uses the task-local Python mirror for post-repair diagnostics. The pinned Racket program remains the production label authority; source-bound Racket receipts are retained separately by the shared check battery and shortcut witness.
