F1: Provide a stable staged-runtime root API

Symptom: a task test and audit that searched ancestors for repository markers passed in the author checkout but failed before collection in the copied task-test runtime. Evidence: `checks/public_eval_981571dc-tests-before/task-tests.log`. Suggested change: expose a small supported `reviewer_support.repo_root()` helper or an explicit environment variable in staged runs, and document it as the only portable root-discovery mechanism.

F2: Prevent cross-task pytest basename collisions

Symptom: collecting two task suites together imported both `tests/test_family.py` files as the same top-level module. The final task-specific second filename passes beside the frozen first filename in `checks/combined/pytest.log`. Suggested change: generate task-specific test filenames by default and keep `--import-mode=importlib` in every multi-target test wrapper.
