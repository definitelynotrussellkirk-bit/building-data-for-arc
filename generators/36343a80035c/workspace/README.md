# Review probes

The selected implementation remains `../generator.py`. These scripts are not
selected automatically and do not modify the audited targets.

`topology_probe.py` independently floods border-connected zeros, tests a small
rival bank, checks compact canonical/counterexample fixtures through Racket,
counts shape/input/output diversity, and probes one-cell breaches and recoloring.
Use it only for the declared background-0 / output-8 / cardinal-connectivity task
contract. `test_topology_probe.py` supplies 16 helper/fixture tests.

`audit_targets.py` replays the two findings-only audits for
`0be8ff9b4144` and `e2c0324ce778`. It records exact overrides, class sequences,
concrete lesson counterexamples, and selected-rule parity. It never edits targets.

## Prepare a self-contained execution tree

From the extracted review packet root (Python 3.12+, NumPy, Pillow, pytest):

```bash
python3 setup_racket.py
PYTHONPATH=repo/src python3 - <<'PY'
from pathlib import Path
from arcpuzzles import Catalog
from arcpuzzles.runtime import prepare_runtime
prepare_runtime(Catalog(Path('repo').resolve()), Path('.review/runtimes/replay'),
                '36343a80035c')
PY
```

The destination must be new/empty. `prepare_runtime` copies code and data;
it does not import a neighboring checkout. The stock mapping includes selected
task tests but not new workspace files; invoke workspace scripts explicitly.
The wrapper below changes its working directory to `repo` and selects the local
verified Racket runtime, which explains the `../` paths:

```bash
python3 run_with_racket.py python3 generators/36343a80035c/workspace/topology_probe.py \
  --runtime ../.review/runtimes/replay --per-band 200 --racket-per-band 20 \
  --require-witnesses --out ../checks/topology-replay.json
```

Run focused tests against that copied generator with an explicit import root:

```bash
PYTHONPATH=.review/runtimes/replay python3 -m pytest \
  repo/generators/36343a80035c/tests/test_generator_36343a80035c.py \
  repo/generators/36343a80035c/workspace/test_topology_probe.py -q
```

For an audit, prepare a new runtime for that audit task and pass it to
`audit_targets.py --runtime ... --task TASK --out ...` under the same wrapper.
Detailed commands actually exercised in this review are in the return's
`RESULTS.json`. The baseline false gate and initial failed audit probe are
intentional retained evidence, not silently waived successful checks.
