# Workspace

`lesson_probe.py` is the retained authoring probe for generator 2.0.0. It imports the selected generator declarations, verifies that every claimed canonical shortcut really fits the usable canonical pairs, then checks all four schedule starts, all three difficulty bands, and every legal one-query rotation for surviving declared rivals and missing witnesses.

Run from the packet root:

```bash
python3 run_with_racket.py python3 generators/d3c9fc4479d8/workspace/lesson_probe.py \
  --starts 4 --out ../checks/lesson-probe.json
```

The probe is finite: it tests the declared `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `SEMANTIC_WITNESSES`; it is not a universal proof of induction. Keep alternate drafts and unfinished experiments here, but `../generator.py` remains the selected implementation.
