# Task-local review tools — 8f10b83435aa

The selected implementation is `../generator.py`. These tools are diagnostics, not alternate generators and not a source of admitted labels.

## Majority-contract probe

From the repository root:

```bash
PYTHONPATH=shared/runtime python3 -B generators/8f10b83435aa/workspace/probe_majority_contract.py \
  --per-band 100 --lesson-starts 30 --out ../checks/final-majority-probe.json
```

The probe independently samples the production generator, checks deterministic replay, validates every grid, requires at least three one-panel negatives, three pair-only positives and one triple positive, compares every declared lesson rival with the Python rule mirror, exercises two-demonstration lessons, verifies all exact axes are recoverable from pixels, and checks the mirror against all labeled canonical pairs. It exits nonzero and retains up to 20 small witnesses if any check fails.

This is finite evidence. It does not enumerate every seed, replace authoritative Racket parity, or prove identifiability against undeclared hypotheses. The battery and source-bound lesson census remain the acceptance evidence.

## Regression tests

The portable task-test stage is the supported integration path:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 8f10b83435aa \
  --stage task_tests --timeout 600 --phase after --out ../checks/task-tests
```

The tests under `../tests/` cover canonical parity, exact override observability, invalid-control rejection, threshold-side support, declared shortcut refutation, lesson identifiability, deterministic replay and band-sensitive defaults.
