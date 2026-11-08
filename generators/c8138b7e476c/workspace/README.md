# Workspace

The selected implementation is `../generator.py`; task-local regression tests
are in `../tests/test_generator.py`.

Fast portable qualification from the repository root:

```sh
TERM=dumb PYTHONPATH=shared/runtime \
  python3 -m pytest -q generators/c8138b7e476c/tests/test_generator.py
```

The official battery, lesson census, red test run, synthetic rival-survival
lesson, and final reports are retained under the packet-level `checks/`
directory. Workspace drafts are never automatically selected.
