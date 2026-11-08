# Workspace

The selected implementation is `../generator.py`. This workspace contains a
reusable check for the cyclic-start and joint-support questions the shared
production census does not exhaust.

From an extracted review packet root:

```sh
python3 run_with_racket.py python3 generators/c39bef185e7e/workspace/probe_curriculum.py \
  --seed 17 --out ../checks/curriculum.json
```

Use a new output path. By default this covers all 240 raw schedule starts in
each difficulty band, with three demonstrations and one query. Each of the
four labelled pairs is held out once, preserving the others' order. It reuses
public `Catalog.apply` labels in batches of at most 64 inputs and dynamically
reads `LESSON_COMPETITORS` and `CANONICAL_SHORTCUTS`. Retained evidence includes
the actual source and probe hashes, reference receipts, inputs and labels,
seed/index/band, unique inputs, canonical rival fit, joint axis support,
per-rival verdicts, hook warnings, and exact query-changing counterexamples.

`--band medium` limits the bands; `--period N` changes the explicitly measured
number of starts. `--source PATH` reads an explicit historical generator while
still executing the currently selected canonical rule; its separate source hash
prevents reporting historical samples as current-source evidence. The reviewed
baseline has 20 phases and two demonstrations, which the tool reads from it.

The command exits nonzero on measured ambiguity, hook warnings, mirror
disagreement, or an execution error. It is a direct consecutive-window probe;
use the shared `lesson-census` for production materialization and rejections.
Finite declared-rival evidence is not universal identifiability.

Focused tests are in `../tests/test_curriculum.py`. The packet's portable
`arcpuzzles check c39bef185e7e --stage task_tests` snapshots these files and
records test counts and JUnit evidence. Install pytest in an activated venv:
the isolated runner intentionally disables user-site packages.
