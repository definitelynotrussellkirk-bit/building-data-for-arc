# Task workspace: 5b4fd0a9c80e

The selected implementation is `../generator.py`. Workspace code is diagnostic and
is not selected automatically.

## Independent reference probe

`reference_probe.py` independently reimplements same-color components, raw bbox
cropping, `(area, top, left)` sorting, one-row separation, and floor centering. It
binds its report to the generator and canonical-ledger SHA-256 values, checks every
canonical label, measures the declared canonical shortcuts, materializes complete
three-demo-plus-query lessons in all bands, and scores the generator's live
`LESSON_COMPETITORS` declarations.

From the repository root:

```bash
PYTHONPATH=shared/runtime python3 \
  generators/5b4fd0a9c80e/workspace/reference_probe.py \
  --lessons-per-band 100 --seed-start 700 \
  --out ../checks/reference-probe.json
```

The probe is finite evidence, not a proof of unique induction. The production
sampler and all query rotations are checked separately by the shared
`lesson-census` command.
