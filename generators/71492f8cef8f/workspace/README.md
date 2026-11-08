# Workspace

The selected implementation is `../generator.py`; workspace files are reusable
review aids and are never automatically selected as production code.

## Cyclic lesson-window probe

`lesson_window_probe.py` checks every cyclic start in the generator's declared
schedule for all three difficulty bands. It imports the live declarations from
`generator.py`, materializes the configured demonstrations plus query, and
verifies that every declared semantic rival is already refuted by the demos,
every declared witness is represented, the schedule is pixel-observable, and
`lesson_identifiable` finds no demo-compatible rival that changes the query.

From the packet root:

```bash
python3 run_with_racket.py python3 \
  generators/71492f8cef8f/workspace/lesson_window_probe.py \
  --seeds-per-start 16 \
  --out ../checks/lesson-window-probe.json
```

The probe is finite evidence over declared rivals and witnesses. It does not
establish universal identifiability against undeclared rules.
