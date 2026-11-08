# Workspace for `8b3462620478`

The selected implementation is `../generator.py`. Workspace files are review aids and are never automatically selected.

## Independent beam oracle

`reference_probe.py` intentionally does **not** import the generator. It accepts either a raw grid JSON or an object containing an `input` grid and prints the output plus a trace report.

From the task directory:

```bash
python3 workspace/reference_probe.py counterexamples/first_three_mirrors_only.json
python3 workspace/reference_probe.py counterexamples/first_three_mirrors_only.json --compare-first-three
python3 workspace/reference_probe.py scene.json --mirror-limit 3
python3 workspace/reference_probe.py scene.json --swap-mirrors
```

The oracle uses the pinned semantics: source `2`, adjacent heading `1`, slash mirror `3`, backslash mirror `4`, wall `5`, painted background `8`, and a 500-step fuel cap. `--mirror-limit N` keeps tracing through all mirrors but only lets the first `N` change direction, which is useful for finite-depth shortcut probes.

The retained counterexample demonstrates the strongest canonical-fitting shortcut: reflecting only at the first three mirrors. Its fourth mirror changes nine cells, and focused tests require the independent oracle, saved outputs, and generator behavior to remain consistent.
