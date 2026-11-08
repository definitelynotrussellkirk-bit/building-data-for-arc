# Workspace and reusable probes

The selected implementation is `../generator.py`. The reusable review probe is
`../tests/test_generator.py`; it is written with `reviewer_support.find_root`,
`canonical_pairs`, and a portable import path so it runs both in the repository
and in the isolated task-test runtime.

From the packet root, run the portable task tests with:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 97dd5f3c96b9 \
  --stage task_tests --timeout 600 --phase after --out ../checks/task-tests
```

For a fast direct replay from `repo/`:

```bash
PYTHONPATH=shared/runtime python3 -m pytest -q \
  generators/97dd5f3c96b9/tests/test_generator.py
```

The suite checks all canonical pairs, the historical overlapping-span fixture,
48 default draws per difficulty setting, every exact profile override,
near-miss mutations, semantic rivals/witnesses, global-RNG purity, fresh return
objects, and replay stability across three `PYTHONHASHSEED` values.

The baseline seed reproducer and supported Racket transcript live at
`checks/repro/97dd5f3c96b9/`. Workspace drafts are never automatically selected.

## Proposed parametric extension

`parametric/` contains an unapproved episode-level `connector_color` prototype,
a thin promotion adapter, exact contract, focused tests, and a protected-Racket
evidence writer. It leaves the selected production generator and canonical
rule unchanged. See [`parametric/README.md`](parametric/README.md) for semantics,
commands, output layout, and limits.
