# Workspace

`reference_probe.py` is an independent authoring oracle and distribution audit for `f812a7b32f47`. It does not import production transformation helpers. It can:

- compare the documented bbox-edge rule with all canonical pairs;
- recover the six exact axes from pixels;
- sample easy/medium/hard support and self-check validity;
- compare the intended rule with the canonical-fitting `markers_anywhere` rival; and
- emit an explicit legal disagreement witness.

Example from the packet root:

```bash
python3 run_with_racket.py python3 generators/f812a7b32f47/workspace/reference_probe.py \
  --count 256 --out ../checks/independent-audit.json
```

The selected implementation remains `../generator.py`; workspace files are supplementary evidence and are never automatically selected.
