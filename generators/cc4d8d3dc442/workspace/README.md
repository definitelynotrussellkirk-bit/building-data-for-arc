# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here. The selected implementation is `../generator.py`; workspace drafts are never automatically selected.

`shortcut_witness.py` is a retained deterministic diagnostic for the strongest canonical-compatible shortcut. From the repository root:

```bash
PYTHONPATH=shared/runtime python3 \
  generators/cc4d8d3dc442/workspace/shortcut_witness.py
```

It emits the generated input, recovered axes, region key counts, intended parity output, `one_vs_many` rival output, and every disagreeing cell. Defaults are seed 71 and sample index 5; both may be overridden on the command line.
