# Workspace

`pairing_coverage.py` measures the exact source→target rank permutations emitted
for `K=2..4`. It exists because the ordinary shape/palette diversity checks can
report 100% unique grids while a legend generator still covers only a tiny
subset of its legal bijections.

From the repository root:

```bash
python3 generators/e1e7c467196f/workspace/pairing_coverage.py \
  --seeds 256 --sample-indices 12 --out ../checks/pairing-coverage.json
```

Pass `--generator PATH` to compare another copy of the generator. The selected
implementation remains `../generator.py`; workspace scripts are diagnostic only.

`run_task_tests.py` builds a temporary runtime overlay and runs the task-local
pytest file without modifying the repository runtime tree:

```bash
python3 generators/e1e7c467196f/workspace/run_task_tests.py
```
