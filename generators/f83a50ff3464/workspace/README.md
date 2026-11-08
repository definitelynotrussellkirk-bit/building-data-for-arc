# Workspace

`shortcut_probe.py` is a reproducible reviewer aid for the selected generator.
It loads the canonical examples and the live generator, verifies that every
registered canonical shortcut fits all source pairs, finds the first generated
counterexample for every semantic witness, and checks every scheduled
four-demonstration window in all three difficulty bands.

Run from any directory:

```bash
python3 repo/generators/f83a50ff3464/workspace/shortcut_probe.py \
  > checks/shortcut-probe.json
```

The selected implementation remains `../generator.py`; workspace programs are
not imported by generation or by the catalog.
