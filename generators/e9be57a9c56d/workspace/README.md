# Workspace

`reference_probe.py` is a reusable, independent review tool for this task. It deliberately does not import the production parser, mirror, rivals, or observability helpers.

From the repository root:

```bash
PYTHONPATH=src python3 generators/e9be57a9c56d/workspace/reference_probe.py \
  --count 128 --seed 1701 --difficulty medium \
  --out ../checks/reference-probe-medium.json
```

It can:

- load canonical pairs and verify that declared shortcuts fit them;
- independently parse the largest-template/singleton-marker grammar;
- compute the intended template-chain output;
- compute total fixed-color and endpoint-only rival outputs;
- extract profiles and semantic observables;
- execute the selected Racket rule through the public runner for parity checks;
- audit uniqueness, validity, profile floors, orientation/anchor coverage, and shortcut counterexample counts.

The selected implementation is `../generator.py`. Workspace code is review support and is never automatically selected as the generator or label authority.
