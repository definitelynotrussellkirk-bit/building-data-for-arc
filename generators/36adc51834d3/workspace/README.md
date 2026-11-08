# Review workspace: 36adc51834d3

The selected implementation is `../generator.py`; focused executable regressions are in `../tests/test_generator.py`.

## Fast local verification

From `repo/`:

```bash
python3 ../run_with_racket.py python3 -m pytest generators/36adc51834d3/tests -q
python3 ../run_with_racket.py python3 -m arcpuzzles check 36adc51834d3 \
  --battery --timeout 4000 --phase after --out ../checks/after
```

## Source-bound extended lesson probe

Prepare a portable runtime from `repo/`:

```bash
PYTHONPATH=src python3 - <<'PY'
from pathlib import Path
from arcpuzzles.catalog import Catalog
from arcpuzzles.runtime import prepare_runtime
prepare_runtime(Catalog(), Path('../checks/lesson-runtime-final'),
                task_ids=['36adc51834d3'])
PY
```

Then run from the packet root. `env -C` is deliberate: a login shell may reset the Racket `PATH` injected by `run_with_racket.py`.

```bash
python3 run_with_racket.py env -C checks/lesson-runtime-final \
  python3 scripts/generator_semantic_gate.py 36adc51834d3 \
  --per-band 200 --lessons 300 --strict --require-contract \
  --require-rival-witness --require-shortcut-counterexample \
  --json-out /absolute/path/to/checks/extended-semantic-final3.json
```

`--lessons 300` is split into 100 lessons per difficulty band. The gate uses four demonstrations plus one query, a pinned seed plan, and sample-index stride 11, so all cyclic command starts are exercised. Retain both failures and final reports; the one-in-300 command-crop bug is a useful regression.
