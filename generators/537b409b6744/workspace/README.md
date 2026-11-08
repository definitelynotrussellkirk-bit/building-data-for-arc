# Workspace

`reference_probe.py` is an independent Python oracle and diagnostic helper for task `537b409b6744`. It extracts modal background and same-color components, reproduces candidate ranking, computes the intended output and two explicit rivals (`farthest_candidate_output`, `no_growth_output`), recovers public axes, and summarizes batches. It is used by task-local tests but is not selected production code.

Run focused tests from the packet root:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 537b409b6744 \
  --stage task_tests --phase after --out ../checks/task-tests
```

The selected implementation remains `../generator.py`; workspace helpers are never automatically selected.
