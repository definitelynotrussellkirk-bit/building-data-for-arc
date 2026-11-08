# Workspace

`counterexample_probe.py` is a reusable source-bound probe for the strongest canonical-fitting shortcut. It generates a lawful off-center-pivot case, computes the intended point-reflection output and the geometric-grid-center rival output, records the generator/rule hashes, and exits nonzero if they do not actually disagree.

Run from `repo/`:

```bash
PYTHONPATH=shared/runtime python3 generators/38200022d1b7/workspace/counterexample_probe.py \
  --out ../checks/question-generator-shortcuts/counterexample.json
```

The selected implementation remains `../generator.py`; workspace tools are not automatically selected.
