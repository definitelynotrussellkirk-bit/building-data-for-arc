# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Exhaustive exact-control support probe

From the packet root:

```sh
python3 run_with_racket.py python3 generators/8e7f766c96bf/workspace/probe_override_support.py --out ../checks/override-support-new.json
```

The script reads AXES dynamically, tests their complete finite product across
three seeds and all difficulty bands, and independently recovers shapes/counts
from pixels. It reports output/control mismatches, unexpected exceptions, missing
incompatibility records and support that changes with seed/band. It reads no
reference labels or solve records. Use a new output path for each source version.
The review's 924 configurations produced 7,992 lawful successes and 324 explicit
shelf rejections in 8,316 calls, with zero findings. A rejection describes this
sampler's supported shelf family, not all geometrically possible arrangements.
