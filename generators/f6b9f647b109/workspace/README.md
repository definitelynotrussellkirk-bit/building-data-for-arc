# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Schedule audit

Run the retained task-local checker after schedule changes:

```bash
python3 workspace/analyze_schedule.py
python3 workspace/analyze_schedule.py --json
```

It imports the selected generator, materializes one full schedule period, and checks factor support, every cyclic four-demo window, canonical-size anchor counts, and query recombination.
