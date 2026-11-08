# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Consecutive-window curriculum probe

`probe_schedule_windows.py` exhaustively checks a requested set of consecutive
teaching-window starts. For each difficulty band it builds the configured number
of demonstrations, places the next sample in the query position, and reports any
declared semantic rival that still fits every demonstration but changes the query.
This complements random lesson sampling and query rotation; it is especially useful
for periodic schedules.

From the repository root:

```bash
PYTHONPATH=shared/runtime python \
  generators/91c488d9ffdc/workspace/probe_schedule_windows.py \
  --starts 18 --require-identifiable \
  --out ../checks/schedule-window-probe.json
```
