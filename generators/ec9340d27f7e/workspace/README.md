# Workspace tools for `ec9340d27f7e`

The selected implementation is `../generator.py`. Workspace files are support artifacts and are never automatically selected.

## `semantic_probe.py`

Fast deterministic census for future reviewers. It imports the selected generator, samples easy/medium/hard bands, checks all generated grids, and reports:

- schedule-profile coverage,
- strict canonical-anchor fraction,
- witness firing counts,
- per-rival disagreement counts,
- rolling lesson-identifiability failures,
- self-check or oracle failures.

Run from `repo/`:

```bash
PYTHONPATH=shared/runtime python3 \
  generators/ec9340d27f7e/workspace/semantic_probe.py \
  --samples-per-band 32 \
  --json-out generators/ec9340d27f7e/workspace/semantic_probe_report.json
```

A nonzero exit means at least one declared profile, witness, rival, lesson, self-check, or oracle requirement failed. The committed `semantic_probe_report.json` is a reproducible 96-draw review snapshot, not a substitute for the official Racket-backed battery.
