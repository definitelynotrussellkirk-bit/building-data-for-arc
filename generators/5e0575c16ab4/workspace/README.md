# Workspace

The selected implementation is `../generator.py`; workspace files are reusable
review probes and are never selected automatically.

## Shortcut probe

Run from the packet root:

```sh
python3 repo/generators/5e0575c16ab4/workspace/shortcut_probe.py \
  --out repo/generators/5e0575c16ab4/workspace/shortcut_counterexample.json
```

The probe compares the intended global-count rule with the strongest canonical-
fitting shortcut, row-local pairing. It checks a hand-built witness and a normal
`global_repeat` generator draw, asserts both disagreements, and writes the exact
inputs, outputs, and disagreement cells as JSON.
