# Workspace

The selected implementation is `../generator.py`; workspace files are supporting probes and are not selected automatically.

## `transform_ambiguity_probe.py`

Independently reparses the three panels, enumerates all eight D4 explanations, and counts distinct fitting query outputs. It does not trust the generator's private analyzer.

From `repo/`:

```bash
PYTHONPATH=shared/runtime:. python3 \
  generators/75b8cb3d5e9b/workspace/transform_ambiguity_probe.py \
  --draws-per-band 500 \
  --seed-base 300000 \
  --out generators/75b8cb3d5e9b/workspace/final_transform_ambiguity.json
```

Exit status is nonzero if any sampled input fails `self_check`, has multiple defensible query outputs, or has fewer than eight query orientations. The report explicitly remains a finite generated-domain census, not a proof of universal induction.
