# Workspace

The selected implementation is `../generator.py`; workspace files are reviewer
probes and are never automatically selected for training.

## Exhaustive schedule probe

`./schedule_probe.py` complements the shared lesson census by testing every
cyclic start in this generator's six-slot curriculum and holding out each of the
four pairs as the query. It uses the selected generator's own
`LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, and `lesson_identifiable` hook.

From the packet root:

```bash
python3 run_with_racket.py python3 \
  generators/8dbffe99308f/workspace/schedule_probe.py \
  --cycles 2 --out ../checks/schedule-probe.json
```

A pass is finite evidence against the declared rivals, not a proof of unique
induction against every imaginable rule. Increase `--cycles` or supply more
`--seeds` when changing the schedule or random layout logic.
