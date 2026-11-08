# b71c45e9a3c0 authoring probes

These helpers are independent of the production generator's component, oracle,
and axis-observation functions. They are review aids; the canonical Racket rule
remains label authority.

From `repo/`:

```bash
PYTHONPATH=src:shared/runtime python3 generators/b71c45e9a3c0/workspace/reference_probe.py \
  --count 128 --out ../checks/b71c45e9a3c0_independent_probe.json

PYTHONPATH=src:shared/runtime python3 generators/b71c45e9a3c0/workspace/layout_probe.py \
  --count 128 --out ../checks/layout-diversity.json
```

`reference_probe.py` checks canonical acceptance/oracle parity, determinism,
realized axis domains, profile support, and disagreement with the two declared
rivals. `layout_probe.py` counts bboxes that have nonzero margin on all four
sides, guarding against an accidental "every object is pinned to a grid corner"
shortcut.

Both probes are finite diagnostics. They establish behavior only for the stated
seeds, counts, generator hash, and declared rivals; they are not proofs of
universal identifiability.
