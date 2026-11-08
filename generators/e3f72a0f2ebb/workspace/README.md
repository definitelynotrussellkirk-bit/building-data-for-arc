# Outline review tools

The selected implementation is `../generator.py`; these tools do not select
alternate generators or edit shared checks.

Run commands from the extracted packet's `WORK` directory. The wrapper runs
the payload from `WORK/repo`. Prepare the bundled authority with
`python3 setup_racket.py`. Use a Python 3.12+ environment containing pytest,
NumPy and Pillow for the portable task-test stage.

## Focused regressions

```bash
python3 run_with_racket.py python3 -m arcpuzzles check e3f72a0f2ebb --stage task_tests --timeout 600 --phase after --out ../checks/task-tests-next
```

Use a fresh output directory. If dependencies exist only in the user site, the
isolated test stage will reject that environment; use an explicit virtualenv
interpreter instead. The review's exact isolated-environment setup is retained
in `checks/environment/pytest-venv.json` of its return.

## Distribution and rival support

```bash
python3 run_with_racket.py python3 generators/e3f72a0f2ebb/workspace/probe_outline_support.py --self-test
python3 run_with_racket.py python3 generators/e3f72a0f2ebb/workspace/probe_outline_support.py --racket-witnesses --out ../checks/support-next.json
```

Read [README_outline_support.md](README_outline_support.md) for sampling
parameters, count definitions, failure retention and authority limitations.
The default scan does not substitute for a production lesson census.

## Lawful endpoint evidence

```bash
python3 run_with_racket.py python3 generators/e3f72a0f2ebb/workspace/prove_lawful_endpoints.py --out ../checks/lawful-endpoints-next.json
```

This obtains actual Racket outputs for twelve explicit lawful endpoint inputs,
and checks six invalid controls. It does not suppress generic defect-lint
warnings. A nonzero exit and saved report require inspection. Existing output
files are protected from overwriting.

## Lesson assembly, including rotations

```bash
python3 run_with_racket.py python3 -m arcpuzzles lesson-census e3f72a0f2ebb --per-band 100 --rotate-query --timeout 1800 --out ../checks/lesson-census-next.json
python3 run_with_racket.py python3 -m arcpuzzles lesson-census e3f72a0f2ebb --enumerate-schedule-period --schedule-seed 0 --timeout 600 --out ../checks/schedule-census-next.json
```

The first command checks 300 seeded lessons. The second covers the finite
four-phase schedule at one seed; its overlapping windows are a different
population. Each uses four demonstrations plus one query. Report production
and rotation verdicts separately, with all limits in the saved receipts.
