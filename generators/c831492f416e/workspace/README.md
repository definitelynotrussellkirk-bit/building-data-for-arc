# Semantic profile audit

`profile_audit.py` is a task-local, read-only census for the selected
implementation in `../generator.py`. It checks:

- Python mirror parity on all five canonical input/output pairs;
- complete and exactly observable five-profile scheduling in every band;
- `self_check`, strict-manifold rate, and endpoint-overwrite safety;
- lesson-level refutation of every declared rival rule;
- input/output uniqueness and shape/palette signatures.

Run from the repository root:

```bash
PYTHONPATH=shared/runtime python3 generators/c831492f416e/workspace/profile_audit.py \
  --seeds 100 \
  --out generators/c831492f416e/workspace/profile_audit.json
```

The report is deterministic for a fixed source tree and exits nonzero on any
semantic failure. Workspace artifacts are not automatically selected; the
active implementation remains `../generator.py`.
