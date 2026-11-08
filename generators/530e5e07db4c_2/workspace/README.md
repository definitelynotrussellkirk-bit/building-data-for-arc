# Workspace

The selected implementation is `../generator.py`; workspace programs are diagnostic and are never selected automatically.

## `curriculum_probe.py`

This source-bound probe exhaustively checks cyclic three-demonstration starts for a chosen seed set, records which named rival each demonstration refutes, measures profile and gray-object coverage, and reports which rivals fit all canonical pairs.

From the extracted packet root:

```bash
python3 run_with_racket.py python3 generators/530e5e07db4c_2/workspace/curriculum_probe.py \
  --out ../checks/curriculum-probe.json
```

A nonzero exit means at least one checked lesson left a declared rival alive or the task hook reported ambiguity.
