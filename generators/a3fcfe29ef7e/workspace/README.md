# Workspace

The selected implementation is `../generator.py`.

`probe_schedule_contract.py` is a model-free reproducibility tool.  It enumerates
every declared cyclic schedule start in every difficulty band, rotates each
materialized pair through the query position, and calls the executable
`lesson_identifiable` contract.  Example:

```bash
python3 generators/a3fcfe29ef7e/workspace/probe_schedule_contract.py \
  --repo-root . --out ../checks/schedule-probe.json
```

Workspace drafts are never automatically selected.
