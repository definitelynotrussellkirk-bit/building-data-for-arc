# Workspace

`curriculum_probe.py` is a task-local reviewer aid. It generates consecutive
four-example lessons in every difficulty band, checks schedule coverage and
strict-anchor count, invokes `lesson_identifiable`, verifies that every declared
rival receives a counterexample, and emits a JSON-safe report.

From the repository root:

```bash
PYTHONPATH=shared/runtime python3 \
  generators/91b531b5d3f4/workspace/curriculum_probe.py \
  --seed 303 --windows 12 --out ../checks/curriculum_probe.json

PYTHONPATH=shared/runtime python3 \
  generators/91b531b5d3f4/workspace/test_curriculum_probe.py
```

This fast probe does not execute Racket and is not a substitute for
`arcpuzzles check ... --battery`. Keep alternate drafts, reproducers, and
unfinished experiments here; the selected implementation remains
`../generator.py`.
