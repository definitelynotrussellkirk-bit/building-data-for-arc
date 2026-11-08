# Workspace and replay map

The selected implementation is `../generator.py`; task regressions are in `../tests/test_generator.py`. Workspace drafts are never automatically selected.

Final reviewed identity:

- generator SHA-256: `1e242e04c710107969f6da280291342ae2fe6f0dc4da2a7eb7652e17c85bbe51`
- rule hash: `8cfb5cf9c2c4`
- version: `3.0.0`

From the packet root, replay the focused portable tests with:

```text
python3 run_with_racket.py python3 -m arcpuzzles check a9c4475d7cda --stage task_tests --timeout 600 --phase after --out ../checks/task-tests-replay
```

Replay the full repository contract with:

```text
python3 run_with_racket.py python3 -m arcpuzzles check a9c4475d7cda --battery --timeout 4000 --phase after --out ../checks/after-replay
```

The review return retains:

- pre-fix RED tests: `checks/tdd-red.log`
- final battery aggregate: `checks/after/checks/a9c4475d7cda_after_battery_summary.json`
- exact-two Racket counterexample: `checks/shortcut-a9c4475d7cda/counterexample.json`
- 300-lesson census: `checks/lesson-census.json`
- final visible-only solve: `solve/summary.json`

Do not infer universal identifiability from the finite rival census. Any future semantic expansion should add an executable rival and a per-lesson witness before changing production sampling.
