# Workspace

The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Axis-position shortcut probe

`axis_offset_shortcut_probe.py` is an independent regression tool for the defect repaired in version 4.0.0. It does not call the generator's declared rival implementation. It samples the production defaults, measures joint `(source_mode, axis_offset)` support, evaluates every overlapping four-example lesson window, and checks a lawful explicit counterexample.

From the packet root:

```bash
python3 repo/generators/4ee97d4d2321/workspace/axis_offset_shortcut_probe.py \
  --draws-per-band 100 \
  --seed 8700 \
  --out checks/axis-offset-shortcut-after.json
```

A pass requires all 20 joint pairs in each band, zero lesson windows on which the shortcut fits every demonstration, and an answer-changing explicit counterexample. The focused tool test is:

```bash
python3 -m pytest -q \
  repo/generators/4ee97d4d2321/workspace/tests/test_axis_offset_shortcut_probe.py
```
