# Workspace

`lesson_probe.py` is a source-bound semantic audit for this task. It prepares an immutable portable runtime from the selected checkout, materializes lessons through the canonical Racket runner, iterates the generator's actual `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, and reports unique inputs, profile/corner counts, rival disagreements, survivors, and exact first counterexamples.

Final review invocation from the packet root:

```sh
python3 run_with_racket.py python3 generators/dd038eb3d459/workspace/lesson_probe.py \
  --library . --lessons-per-band 100 --out ../checks/lesson-probe.json
```

The selected implementation remains `../generator.py`; workspace tools are evidence helpers and are never selected as generators.
