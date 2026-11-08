# Workspace

`reference_probe.py` is the reusable, source-bound review probe for this task. It provides:

- an independent Python onion-depth/crop transliteration;
- a canonical-fitting wrong rule that peels exact colors separately;
- canonical-profile, component-size, uniqueness, and witness measurements;
- public `Catalog.apply` parity against the selected Racket authority.

Run from the packet root through the prepared runtime:

```sh
python3 run_with_racket.py python3 \
  generators/bd8613daf5b1/workspace/reference_probe.py \
  --count 240 --out ../checks/reference-probe.json
```

The selected implementation is `../generator.py`. Workspace probes are diagnostic and are never automatically selected as production code.
