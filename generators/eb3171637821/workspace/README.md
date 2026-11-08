# Workspace

The selected implementation is `../generator.py`. These source-bound helpers are retained for future reviewers:

- `reference_probe.py` independently analyzes divider lattices, computes the intended output and line-count rival, loads canonical pairs, and checks live Racket parity without importing private runner functions.
- `audit_lessons.py` imports the generator's live `LESSON_COMPETITORS` declarations and checks every consecutive three-demo/query window over configurable seeds and starts.

Representative commands from the packet root:

```sh
cd repo
PYTHONPATH=shared/runtime python3 generators/eb3171637821/workspace/audit_lessons.py \
  --seeds 20 --starts 12 --n-demos 3 --out ../checks/cyclic-lesson-audit.json
PYTHONPATH=shared/runtime python3 -m pytest -q generators/eb3171637821/tests/test_generator.py
```

Workspace helpers are evidence and review tools; they are never automatically selected as production generators.
