# Workspace

`reference_probe.py` is an independent Python mirror, rival-rule library, and
repeatable distribution audit for this generator. It deliberately does not
import production geometry helpers. The canonical Racket program remains output
authority.

Run a local audit from the repository root:

```bash
PYTHONPATH=shared/runtime python3 generators/4e102ec13fc8/workspace/reference_probe.py \
  --count 128 --out generators/4e102ec13fc8/workspace/audit.json
```

Use `--generator PATH` to replay the same probes against a copied or patched
implementation.
