# Workspace

The selected implementation is `../generator.py`. Workspace drafts and probes
are reviewer tooling; they are never automatically selected for generation.

- `baseline-generator-v2.2.0.py` preserves the assigned source before repair.
- `lesson_probe.py` audits every query rotation of overlapping four-pair lesson
  windows against the generator's current `LESSON_COMPETITORS`. It retains an
  exact lesson whenever a rival fits all three demonstrations but disagrees on
  the held-out query.

From the extracted packet root:

```sh
python3 run_with_racket.py python3 \
  generators/0bb8813a21dc/workspace/lesson_probe.py \
  --starts 100 --out ../checks/lesson-window-probe.json
```

The probe uses the source-bound Python `rule_mirror`; pair it with the battery's
`rule_smoke` and `authority_sync` stages for canonical Racket parity evidence.
