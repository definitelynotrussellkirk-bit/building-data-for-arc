# Workspace

`lesson_probe.py` is the retained source-bound whole-lesson census. From `repo/`:

```bash
PYTHONPATH=src python3 generators/0da360b839c1/workspace/lesson_probe.py \
  --lessons-per-band 100 \
  --out ../checks/lesson_probe_100_per_band.json
```

It reads the selected generator's actual rival declarations, verifies declared canonical shortcuts against canonical pairs, mirrors production 4-demo + 1-query assembly, and tests both the pinned sampler and every cyclic start of the period-four schedule. Counts distinguish unique inputs from overlapping lesson pair occurrences. Its claims are finite and do not establish model gains.

The selected implementation remains `../generator.py`; workspace drafts are never automatically selected.
