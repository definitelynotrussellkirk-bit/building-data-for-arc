# Workspace

`lesson_probe.py` is a source-bound, Racket-backed reviewer replay tool for this task. It dynamically iterates the selected generator's `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, verifies canonical shortcut fit, labels all generated inputs through the public canonical `Catalog.apply` API, enumerates all five cyclic starts in all three bands, and rotates each four-pair instance through every query position.

Run it from a staged runtime or the repository root with the packet's Racket wrapper:

```bash
python3 run_with_racket.py python3 generators/0c4c1974cbf2/workspace/lesson_probe.py \
  --out ../checks/lesson-probe.json
```

The finite rival set is diagnostic, not a proof of unique induction. The standard `arcpuzzles lesson-census` remains the production-sampler check.
