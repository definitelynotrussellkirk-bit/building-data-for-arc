# Workspace

`lesson_schedule_probe.py` is a cheap, Racket-free preflight for future edits.
It materializes every five-pair cyclic start requested in each difficulty band,
holds out each pair once, and reports any declared rival that still fits all
four demonstrations. The generator's task-local regression suite independently
checks its assumptions and a real-Racket parity sample; the full
`arcpuzzles lesson-census` remains the authoritative source-bound evidence.

Example from the repository root:

```sh
PYTHONPATH=shared/runtime python3 generators/4d3c5600ffbd/workspace/lesson_schedule_probe.py \
  --starts 10 --out ../checks/lesson-schedule-probe.json
```
