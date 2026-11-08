# Workspace

`shortcut_probe.py` is a reusable lesson-level audit for this task. It imports
`CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS` from the current generator rather
than copying rival names, verifies that claimed canonical shortcuts fit every
canonical pair, and checks cyclic four-demo-plus-query windows across all bands.

From the packet root:

```bash
python3 repo/generators/8fca6bf05488/workspace/shortcut_probe.py \
  --starts 16 --seeds 17 808 5150 --assert-clean \
  --out checks/shortcut-probe.json
```

The retained run checked 144 lessons and found no coverage, hook, or surviving-
rival failures. This is a finite declared-rival test, not a proof that no other
shortcut exists. The selected implementation remains `../generator.py`.
