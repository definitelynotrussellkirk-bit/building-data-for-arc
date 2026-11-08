# Workspace

`lesson_probe.py` is the retained source-bound lesson census for this review. It imports the selected generator, iterates the generator's actual `LESSON_COMPETITORS`, `CANONICAL_SHORTCUTS`, and witness declarations, checks every cyclic start in a deterministic range, and records unique-input counts separately from overlapping lesson windows.

Run from the repository root:

```bash
PYTHONPATH=shared/runtime:src python3 generators/bb432515d2e6/workspace/lesson_probe.py \
  --starts-per-band 100 --seed 20261003 \
  --out ../checks/lesson-probe.json
```

Keep alternate drafts, reproducers, and unfinished experiments here. The selected implementation is `../generator.py`; workspace drafts are never automatically selected.
