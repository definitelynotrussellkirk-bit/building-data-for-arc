# Task-local review tools — 9d0a6f959321

The selected implementation is `../generator.py`. Workspace files are review aids, not alternate admitted generators.

## Contract probe

`contract_probe.py` gives future reviewers a fast, source-bound JSON summary of the contracts most likely to regress:

```bash
PYTHONPATH=repo/shared/runtime python3 \
  repo/generators/9d0a6f959321/workspace/contract_probe.py \
  --samples-per-band 48 --starts 12 --out /tmp/9d0a6f959321-contract.json
```

It imports the declarations from the generator rather than copying rival names. It checks deterministic replay, the six exact override profiles, `self_check`, an independent component-level rule mirror, witness/rival coverage, 3-demo-plus-query production lessons, and every cyclic query rotation of those four-pair lessons. It exits nonzero on any failure and records the generator SHA-256 and rule hash. The final retained run checked 144 generated grids, 36 production lessons, and 144 rotations with no failures (`checks/contract-probe-final.json`).

## Baseline snapshot

`original_generator_v2_0_2.py` is the unmodified assigned baseline used for red tests and the retained lesson-shortcut reproducer. It is not selected automatically and should not be copied over `../generator.py`.

## Standard qualification

From the extracted packet root:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 9d0a6f959321 \
  --battery --resume --timeout 4000 --out ../checks/after
python3 run_with_racket.py python3 -m arcpuzzles check 9d0a6f959321 \
  --stage task_tests --timeout 600 --phase after --out ../checks/task-tests
python3 run_with_racket.py python3 -m arcpuzzles lesson-census 9d0a6f959321 \
  --per-band 100 --rotate-query --timeout 1800 --out ../checks/lesson-census.json
```

Use new output paths after source changes. A finite rival census establishes only the declared contract; it does not certify uniqueness against undeclared hypotheses.
