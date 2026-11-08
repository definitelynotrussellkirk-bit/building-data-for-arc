# Workspace

`profile_audit.py` is a task-local, read-only semantic census for the selected
implementation in `../generator.py`. It verifies:

- all four scheduled profiles are produced and exactly observable;
- every draw passes `self_check`;
- no pair endpoint lies on another segment;
- every four-demo lesson refutes all declared rivals;
- shape/palette signatures and input/output uniqueness remain visible.

Run from the repository root:

```bash
PYTHONPATH=shared/runtime python3 generators/f44596002946/workspace/profile_audit.py \
  --seeds 100 --out generators/f44596002946/workspace/profile_audit.json
```

The JSON output is reproducible and exits nonzero on any semantic failure.
Workspace artifacts are not automatically selected; the implementation remains
`../generator.py`.
