# Reusable task review tools

These tools inspect or generate authoring evidence. They expose reference labels
and must stay closed during a visible-only solve. Run from the extracted packet
root with a Python environment containing pytest, NumPy, and Pillow. The packet's
`run_with_racket.py` sets the public API paths and changes the payload cwd to `repo`.

## Racket-backed exact-override lesson probe

The shared census supports production sampling and query rotations but has no
override argument. `verify_override_lessons.py` fills that gap with raw consecutive
draws, Racket labels through public `Catalog.apply`, cached predictions from all
three actual rival namespaces, every 3-demo/1-query holdout, and source hashes.
It does not reproduce production rejection/resampling. Existing outputs are
refused so failed and earlier results are not accidentally replaced.

```bash
python3 run_with_racket.py python3 generators/b86607f34b8b/workspace/verify_override_lessons.py --out ../checks/new-override-lessons.json
python3 run_with_racket.py python3 generators/b86607f34b8b/workspace/verify_override_lessons.py --case '{"grid_h":9,"grid_w":9,"n_colors":4}' --seed 23 --starts 6 --out ../checks/new-joint-lessons.json
```

Defaults cover exact counts 3, 4, 5, three difficulty bands, seed 0, and starts
0..5 (81 calls, overlapping 54 windows, 216 rotations). A rival surviving all
pairs is reported separately from a rival that fits demonstrations but disagrees
with the query; the former is not evidence that the rule has been taught.

## Exact-control and structural contract probe

`contract_review/probe_controls.py` discovers the current generator dynamically,
records source identity, checks requested observable values and deterministic
replay, and exercises malformed legend cases. Use `--help` and the accompanying
README for repeatable `--case`, `--reject-case`, and `--sample-index` arguments.
Its diagnostic labels do not replace Racket authority.

## Independent closure oracle and fixed authority cases

`semantic_review/closure_diagnostics.py` is an independent set-based diagnostic
mirror with explicit rivals and a small CLI. `authority_fixtures.json` contains
11 Racket-labeled cases; `three_tie_fixture.json` retains the equal-mode tie
witness. The tests consume fixed authority outputs, iterate live rival
declarations, and cover visible effects, canonical fit, overrides, and cyclic
lesson sufficiency. The public production census remains the authoritative
generated-label check.

```bash
python3 run_with_racket.py python3 -m pytest -q generators/b86607f34b8b/tests
python3 run_with_racket.py python3 -m arcpuzzles lesson-census b86607f34b8b --per-band 100 --rotate-query --period 6 --timeout 1800 --out ../checks/new-census.json
```

## Reproducing the environment fallback

The task-test runtime intentionally removes user-site packages. This machine's
pytest was user-site-only, so the first task-test command failed before discovery.
`prepare_review_env.py` creates a new isolated environment from already installed
host distributions and verifies imports under Python `-I`, without networking.
It is a same-machine fallback, not a general package installer.

```bash
python3 repo/generators/b86607f34b8b/workspace/prepare_review_env.py --env .venv --out checks/runtime.json
.venv/bin/python run_with_racket.py ../.venv/bin/python -m arcpuzzles check b86607f34b8b --stage task_tests --timeout 600 --phase after --out ../checks/new-task-tests
```

`audit_support/` retains replay helpers for the findings-only audit of
`364829da8490`; the second audit has its self-contained probe under `checks/audit/`
in the returned evidence. These helpers never edit an audit target.
