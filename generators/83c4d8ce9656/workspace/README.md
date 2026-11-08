# Workspace tools

Run the task-local tests from the repository root:

```bash
PYTHONPATH=shared/runtime python3 -m pytest -q \
  generators/83c4d8ce9656/tests/test_generator_83c4d8ce9656.py
```

`profile_audit.py` exports `audit_census(generator, seeds=10)`. It checks a
complete scheduled lesson for every seed and band, then reports profile counts,
self-check failures, observer mismatches, identifiability failures, surviving
rivals, and strict canonical-profile hits.
