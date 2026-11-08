# Workspace

`lesson_probe.py` is a source-bound authoring probe for the selected generator.
It loads the generator by file path, iterates the generator's actual
`CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, verifies declared canonical
shortcuts against all labeled canonical pairs, and checks every query rotation
of consecutive four-pair windows.

Example from the repository root:

```bash
PYTHONPATH=shared/runtime:shared python3 \
  generators/2243e48c880b/workspace/lesson_probe.py \
  --starts 36 --seed 2243001 \
  --out ../checks/2243e48c880b-source-probe.json
```

This fast probe labels with `rule_mirror`; retain the public Racket-backed
`arcpuzzles lesson-census` report as the acceptance evidence. Workspace files are
not selected runtime implementations.
