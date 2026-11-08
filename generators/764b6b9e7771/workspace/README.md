# Workspace: 764b6b9e7771

`reference_probe.py` is the reusable task-local observer used by tests and
review evidence. It independently traces the beam, recovers exact public axes,
implements the five named rivals, and exposes helpers for checking complete
three-demo windows. It is deliberately separate from `generator.py` so tests do
not merely assert against the implementation under review.

Typical focused run from `repo/`:

```bash
PYTHONPATH=src:shared/runtime:. python3 -m pytest -q \
  generators/764b6b9e7771/tests
```

The packet's portable command is authoritative for handoff:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 764b6b9e7771 \
  --stage task_tests --timeout 600 --phase after --out ../checks/task-tests
```

The probe may read canonical pairs for regression tests. It must not be used
during either visible-only solve episode.
