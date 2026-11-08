# Alignment coverage tools

The selected production implementation is `../generator.py`. These tools do not
change the Racket rule, approve a generator, or export a training dataset.

## Independent conditional-witness gate

`alignment_gate.py` measures interior-span support independently for horizontal
and vertical axes, evaluates two plausible wrong rules, checks every sliding
four-demo window, and validates labels through the actual canonical Racket rule.
It also exercises eight geometric symmetries for selected draws and writes an
escaped, offline HTML counterexample gallery.

From an extracted review packet root, after applying the return patch:

```bash
python3 setup_racket.py
python3 run_with_racket.py python3 generators/b8d6fabb411e/workspace/alignment_gate.py \
  --per-band 4 --orbit-samples 2 \
  --out ../checks/conditional-quick.json --html ../checks/conditional-quick.html
```

This mode makes 68 Racket applications: eight supplied canonical pairs, twelve
generated draws, and 48 transformed inputs. For the full retained review run:

```bash
python3 run_with_racket.py python3 generators/b8d6fabb411e/workspace/alignment_gate.py \
  --per-band 320 \
  --out ../checks/conditional-full.json --html ../checks/conditional-full.html
```

That makes 1,064 reference applications, not 1,064 distinct challenges. Both
commands refuse to overwrite output files. Exit status: 0 passed; 1 measured
coverage/parity failure; 2 invalid configuration or unavailable runtime.

Without the packet wrapper, set `RACKET_PATH` to a local Racket binary and put
its directory on `PATH`. The tool finds `src/arcpuzzles/runtime.py` relative to
its own location and stages the current library. `--runtime /absolute/tree`
uses an already frozen `prepare_runtime` execution tree instead. Run separate
processes for before and after so Python imports cannot mix implementations.
The setup uses the packet's existing Python ≥3.12, numpy, Pillow and pytest
requirements plus Racket; no network service or new dependency is required.

## Tests

From the packet root, test the independent gate functions directly:

```bash
python3 -m pytest -q repo/generators/b8d6fabb411e/workspace/test_alignment_gate.py
```

The selected generator tests need the inherited execution layout. Prepare an
empty destination and run the mapped file there:

```bash
PYTHONPATH=repo/src python3 - <<'PY'
from pathlib import Path
from arcpuzzles.catalog import Catalog
from arcpuzzles.runtime import prepare_runtime
prepare_runtime(Catalog(Path('repo').resolve()), Path('.review/task-test-runtime').resolve(),
                'b8d6fabb411e')
PY
(cd .review/task-test-runtime && PYTHONPATH=. python3 -m pytest -q tests/test_generator_b8d6fabb411e.py)
```

Expected selected counts: 16 generator tests and five gate tests. The ordinary
12-stage battery and the public repository suite are separate checks; neither
should be described as having executed these new workspace tests.

## Interpretation and limitations

The JSON includes generator version/hash, canonical rule hash, per-case seeds,
input/output hashes, conditional counts and full first counterexamples. All
examples here are **review-only**: reports contain reference answers and wrong
answers, so never send them to training ingestion or model-visible evaluation.

The D4 probes and rival definitions are task-specific. A different task requires
its own justified invariance and branch contracts. Finite rival rejection does
not prove learnability, eliminate every shortcut or measure model performance.
A side-two scene cannot have an interior marker; obligations apply across the
default four-demo schedule, not independently to every pair or forced override.
