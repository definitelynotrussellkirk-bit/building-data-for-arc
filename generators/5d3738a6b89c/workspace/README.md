# Review workspace

`reference_probe.py` is an independent, task-local oracle and audit tool for the
prototype-dictionary rule. It deliberately does not import parsing or stamping
helpers from `../generator.py`, so it can detect generator-side semantic errors.

From the packet root:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=repo/shared/runtime \
  python3 repo/generators/5d3738a6b89c/workspace/reference_probe.py \
  --count 500 --out checks/independent-audit-final.json
```

The report checks every canonical pair, deterministic replay, self-check
acceptance, input uniqueness, all declared branch values, nonoverlapping stamp
footprints, and disagreement with the canonical-fitting first-anchor-only rival.
The selected implementation remains `../generator.py`; workspace code is test
and diagnostic support, not label authority.
