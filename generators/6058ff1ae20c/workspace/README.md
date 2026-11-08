# Workspace

The selected implementation is `../generator.py`.

`lesson_probe.py` is the retained source-bound curriculum census. Run it from the packet root through the runtime wrapper:

```bash
python3 run_with_racket.py python3 generators/6058ff1ae20c/workspace/lesson_probe.py --lessons-per-band 120 --out ../checks/lesson_probe.json
```

It samples complete three-demo-plus-query windows from the actual default schedule, loads competitors from `LESSON_COMPETITORS`, records the generator SHA and sampler, and fails if a competitor survives all demos but changes the query. The current report is `checks/lesson_probe.json`. Workspace experiments are never automatically selected.
