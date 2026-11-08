# Reproduce the rotation repair

The selected implementation is `../generator.py`; this directory contains no
alternate selected draft. Current contracts and limits are in `../notes.md`.

From the outer review packet directory:

```sh
python3 review.py setup
python3 review.py check --stage task_tests --phase after --out ../checks/new-task-tests
python3 review.py check --battery --compact-results --require-rotations-identifiable --phase after --timeout 4000 --out ../checks/new-battery
python3 review.py run python3 -m arcpuzzles lesson-census 9d2f7c9e2ac4 --per-band 100 --rotate-query --timeout 1800 --out ../checks/new-census.json
```

Use new output paths on every changed source. If the task-test preflight reports
missing dependencies, create a venv with pytest, NumPy and Pillow and invoke
`review.py` with that interpreter. The return includes an optional offline
cached-wheel bootstrap helper under `checks/tooling/`; it does not disable
isolation or modify the host interpreter.

Portable regressions are in `../tests/test_rotation_contract.py`. The minimal
retained old-context input and source-bound offset/color witnesses are in
`../counterexamples/`. The return's independent `checks/code-review/review_probe.py`
also enumerates the finite shape banks and cyclic lesson positions, including
an explicit downstream-filtering negative. Actual labels come from the public
Racket-backed check/apply/census commands, not that probe's Python oracle.
