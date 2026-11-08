# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never
automatically selected.

## Shortcut audit

`shortcut_audit.py` is a retained, read-only reviewer probe for the strongest
identified rival: requiring each active color to occur exactly twice globally.
From the repository root:

```bash
PYTHONPATH=shared/runtime python3 \
  generators/c4d63d8b4567/workspace/shortcut_audit.py \
  --seeds 50 --window-starts 8 \
  --out ../checks/probes/global_exactly_two.json
```

The report checks that the rival still fits every canonical pair, that the
Python mirror matches canonical outputs, and that every audited four-example
generated window contains a repeated-color counterexample.
