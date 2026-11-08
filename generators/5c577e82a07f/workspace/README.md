# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never
automatically selected.

## `probe_first_two_shortcut.py`

This source-bound census exercises the canonical shortcut “complete only the
two lowest-valued colors.” It verifies that the shortcut fits every canonical
pair, then checks consecutive three-demo/one-query windows for a query-changing
survivor. Run it from the repository root:

```bash
python3 generators/5c577e82a07f/workspace/probe_first_two_shortcut.py \
  --seeds 100 --starts 24 --difficulty medium \
  --out ../checks/first-two-shortcut-medium.json
```

Repeat with `--difficulty easy` and `hard` after changing the count schedule.
The report records the selected generator hash, exact first examples by status,
window count signatures, and finite-census limitations.
