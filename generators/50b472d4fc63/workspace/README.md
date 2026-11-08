# Workspace

The selected implementation is `../generator.py`; workspace files are independent review tools and are never automatically selected.

- `reference_probe.py` loads the selected generator, reads canonical pairs through the public data file, independently transcribes the authority, measures realized axes/components, and implements the declared plausible rivals.
- `lesson_probe.py` runs a finite lesson audit. It verifies that declared canonical shortcuts really fit all canonical pairs, materializes deterministic sequential windows, checks the fixed query policy, and rotates all four pairs through the query role. Example:

```sh
PYTHONPATH=repo/shared/runtime \
python3 repo/generators/50b472d4fc63/workspace/lesson_probe.py \
  --per-band 100 --out checks/lesson-probe-final.json
```

A pass establishes only finite support against the current declared rivals; it is not a universal induction proof.
