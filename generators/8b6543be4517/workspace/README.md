# Reproducible mirror-generator review

`review_probe.py` copies a standalone runtime from the selected repository,
executes the **actual canonical Racket rule**, and writes source-bound metrics,
exact oracle cases, and a local HTML witness viewer. It never reads a sibling
repository or replaces the canonical labeling path with a Python solver.

From an extracted full review packet, after `python3 setup_racket.py`:

```bash
python3 run_with_racket.py python3 generators/8b6543be4517/workspace/review_probe.py \
  --repo . --out ../checks/my-probe --draws-per-band 1024 \
  --racket-per-band 128 --require-coverage
```

Output must be new. Open `checks/my-probe/witnesses.html` locally; it shows
input, Racket output, and the canonical-fitting zero-only rival side by side.
`report.json` binds the exact generator, rule, canonical file, probe, and Racket
runtime. `oracle_cases.jsonl` retains exact evaluated grids and answers.
A successful technical baseline replay is not a coverage endorsement: use
`--require-coverage` for the new curriculum's required feature families.

To reproduce the frozen baseline with the same measurement code, omit the
coverage requirement and add:

```text
--generator-source ../.review/baseline/repo/generators/8b6543be4517/generator.py
```

The returned `checks/tools/run_task_tests.py` explicitly stages all current
task-local tests and workspace helpers. This is necessary because the packet's
frozen runtime-file map does not automatically add new test files:

```bash
python3 run_with_racket.py python3 ../checks/tools/run_task_tests.py \
  --repo . --out ../checks/my-task-tests
```

Generate a complete ordinary lesson, retaining unapproved research provenance:

```bash
python3 run_with_racket.py python3 -m arcpuzzles generate 8b6543be4517 \
  --count 3 --seed 20261002 --difficulty medium --train 4 --test 2 \
  --allow-unapproved --out ../checks/my-episodes.jsonl
```

The public `generate` command still defaults to three demonstrations. Explicit
four-demo selection matters. These full JSONL episodes include answers/programs
and are private training/evaluation artifacts, **not** label-free challenges.
Use the repository's separate challenge/export interfaces when answer isolation
is required. None of these commands changes approval.
