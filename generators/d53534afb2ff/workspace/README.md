# Workspace

`review_probe.py` is a source-bound distribution and shortcut audit. It reads
the generator's declared `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, checks
canonical-fit claims, materializes exact generated disagreement witnesses,
tests every cyclic start of the four-example lesson schedule, and reports the
number of distinct frame/inside/outside role-palette signatures per profile.
A fixed profile palette is treated as a probe failure.

Example from the repository root:

```bash
python3 generators/d53534afb2ff/workspace/review_probe.py \
  --per-band 100 --out ../checks/review-probe-final.json
```

Alternate drafts and unfinished experiments belong here. The selected
implementation remains `../generator.py`.
