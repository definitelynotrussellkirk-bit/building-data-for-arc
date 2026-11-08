## F1: Verify public authority IDs against the frozen runner

A retained task note falsely reported the `ee_<parent>` namespace as blocked even though the current frozen runner accepts it. Keep a small executable preflight assertion like `checks/public_eval_c4d067a0/runtime-smoke.json` so stale prose cannot turn a resolved compatibility path into recurring manual work.

## F2: Make multi-task pytest collection collision-safe

Both task suites use the basename `test_family.py`, so a direct combined pytest run failed collection while each suite was healthy. Default multi-task verification to `--import-mode=importlib` (evidence: `checks/final-tests-import-collision.txt` and the passing `checks/final-tests.txt`).
