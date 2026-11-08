# Workspace

The selected implementation is `../generator.py`. The files here are authoring
probes; they are never used to generate training labels. Racket remains the
reference authority. Do not open these files during visible-only solving.

## Reusable tools

`semantic_review_probe.py` compares an independent model with canonical pairs,
checks actual declared rivals and the lesson hook, and constructs a compact
top-clipped witness. `--exhaustive-rich` enumerates 756 normalized four-color
key patterns. It defaults to the selected generator in either the library or
the portable execution layout.

From the extracted packet root:

```bash
python3 run_with_racket.py python3 generators/2e663d812b7a/workspace/semantic_review_probe.py --exhaustive-rich --out ../checks/new-semantic-probe.json
python3 run_with_racket.py python3 -m arcpuzzles lesson-census 2e663d812b7a --per-band 100 --train 4 --period 2 --out ../checks/new-lesson-census.json
python3 run_with_racket.py python3 generators/2e663d812b7a/workspace/cyclic_lesson_probe.py --input ../checks/new-lesson-census.json --out ../checks/new-cyclic-lessons.json --canonical
```

`cyclic_lesson_probe.py` consumes a materialized lesson-census report and checks
every pair as the held-out query. It reads rival declarations dynamically,
checks the generator source hash, distinguishes answer-equivalent survivors
from query ambiguity, and cross-checks the generator's lesson hook. Read its
`--help` for the exact input/output options. It reuses retained Racket labels
and does not need more reference executions.

If a return stores large evidence as `.json.gz`, restore it using the return's
`checks/restore_evidence.py` before passing its original `.json` paths to tools.
Always choose a new output filename and retain actual failures.

## Focused tests

```bash
python3 run_with_racket.py python3 -m pytest -q generators/2e663d812b7a/tests
python3 run_with_racket.py python3 -m arcpuzzles check 2e663d812b7a --stage task_tests --phase after --out ../checks/new-task-tests
```

The public task-tests command snapshots the selected source, tests and workspace.
Its isolated child interpreter needs pytest installed in that interpreter's
environment; user-site-only pytest installations are intentionally invisible.
