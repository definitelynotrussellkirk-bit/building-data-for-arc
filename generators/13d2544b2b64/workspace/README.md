# Workspace

The selected implementation is `../generator.py`.

`review_probe.py` is a fast task-local regression tool for future reviews. It checks:

- exact profile observability and balanced schedule coverage;
- canonical Python-mirror parity;
- which declared shortcuts fit every canonical pair;
- whether generated cases provide counterexamples to those shortcuts;
- semantic-witness coverage and four-example lesson identifiability;
- canonical **training** structural support compared with generated pairs.

`rivals` reads all current `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and
`CANONICAL_SHORTCUTS` declarations. Names retain their declaration prefix, so
equal names in different dictionaries do not overwrite each other. Each result
reports canonical fit, the count of generated disagreements, and replayable
execution errors. An exception is a failure, never a counterexample. The existing
`canonical_shortcuts` and `generated_counterexamples` summaries remain available.

The structural comparison uses only labeled canonical **train** pairs; canonical
test pairs still participate in mirror parity and shortcut-fit checks. Including
test labels in structural support can hide a mismatch with the training examples.
This comparison calls the shared `review_diagnostics.compare_structure` helper
and is advisory: inspect `structural_support.comparison.status` and
`disjoint_features` even when `ok` is true. Generated labels in this probe come
from the Python mirror, so these results do not establish independent Racket
parity or replace the central battery.

From the repository root:

```bash
PYTHONPATH=shared/runtime \
  python3 generators/13d2544b2b64/workspace/review_probe.py \
  --seeds 100 --json /tmp/13d2544b2b64-probe.json
```

In an extracted packet, from `WORK/`, use the same prepared Python interpreter
for the wrapper and payload:

```bash
.venv-review/bin/python run_with_racket.py ../.venv-review/bin/python \
  generators/13d2544b2b64/workspace/review_probe.py \
  --seeds 100 --json ../checks/13d2544b2b64-probe.json
```

The probe and focused tests use `reviewer_support.find_root`, `canonical_pairs`,
and `load_selected_generator` to bind data and code to their own tree. They work
in the library layout and in an ordinary runtime without a sibling checkout.
For a runtime prepared with `arcpuzzles workspace --id 13d2544b2b64`, copy this
probe to `generators/13d2544b2b64/workspace/review_probe.py` and the two probe and
generator test files to `tests/13d2544b2b64/`, then run from the runtime root:

```bash
python3 -m pytest --import-mode=importlib tests/13d2544b2b64 -q
PYTHONPATH=. python3 generators/13d2544b2b64/workspace/review_probe.py --seeds 20
```

The public `arcpuzzles check 13d2544b2b64 --stage task_tests` command prepares
its own source snapshot and requires no manual copies. The exact selected Racket
source comparison uses the local catalog mapping or runtime manifest; it still
requires byte-for-byte string equality with every canonical rule variant.
