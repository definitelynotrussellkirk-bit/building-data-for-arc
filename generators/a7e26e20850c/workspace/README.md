# Reviewer workspace: `a7e26e20850c`

`reference_probe.py` is a portable, independent parser/oracle and sampling audit.
It does not import generator internals and never substitutes for the canonical
Racket authority.

From the repository root:

```bash
PYTHONPATH=shared/runtime python3 generators/a7e26e20850c/workspace/reference_probe.py \
  --count 100 --racket --out ../checks/a7e26e20850c-reference-probe.json
```

The report checks canonical labels, determinism, exact-axis observation, the
three-object invariant, schedule coverage, and the canonical-fitting
`first_three_legend_entries` rival. `--racket` is fail-closed: unavailable or
mismatching authority execution exits nonzero instead of falling back to Python.
