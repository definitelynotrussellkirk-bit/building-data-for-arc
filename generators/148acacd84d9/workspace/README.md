# Reusable review probes

## Exhaustive joint exact controls

From the extracted review packet's `WORK` directory, after creating a Python
environment with the documented runtime dependencies:

```bash
.venv-review/bin/python repo/generators/148acacd84d9/workspace/probe_joint_controls.py --out checks/joint-controls-new.json
```

The output path must be new. The probe enumerates height and width 4..12,
foreground count 3..12, and total palette size 3..10 in easy, medium and hard:
6,480 tuples per band, 19,440 total. It observes dimensions and color counts
from pixels independently, checks the validator, verifies structured
incompatibility declarations, repeats a deterministic subset, and binds its
report to source hashes before and after execution. It never generates labels.
The default seed is 123 and sample index is 4; this exhausts the declared value
product at those parameters, not all random seeds or schedule positions.

Use `--limit 16` for a quick baseline, `--band easy` to restrict a band, or
`--seed` and `--sample-index` for another reproducible slice. Exit 0 means the
requested slice passed; exit 1 retains bounded first witnesses and failure
counts. No result replaces Racket reference or lesson checks.

## Portable regression tests

```bash
.venv-review/bin/python run_with_racket.py ../.venv-review/bin/python -m arcpuzzles check 148acacd84d9 --stage task_tests --timeout 600 --phase after --out ../checks/task-tests-new
```

This explicitly collects `tests/test_rotation_contract.py` in the portable
runtime. The root repository suite does not collect these task tests. The
63 cases check controls, validation, diagnostic inputs, determinism, canonical
compatibility, all cyclic starts and query exchanges, all 16 crop placements
including odd centering, the retained wrong-query lessons, and public Racket
labels. The tests use the public `reviewer_support` path helpers, so they work
in a normal repository and copied runtime.

The counterexample retains **intermediate version 2.0.0** inputs and authoritative
answers. Its purpose is to ensure the final lesson hook rejects that historical
ambiguity. It is not a claim that those same inputs are emitted by v2.0.1.
For full production evidence, rerun the public battery with required rotations
and the source-bound `lesson-census` commands recorded in the return.
