# Workspace

The selected implementation is `../generator.py`; workspace files are never
automatically selected.

## `qualification.py`

A portable, source-bound regression probe for future agents. It dynamically
loads the selected generator (or `GENERATOR_UNDER_TEST`), verifies every
declared canonical shortcut against normalized public pairs, then exhaustively
checks all leave-one-out query positions for finite six-pair schedule windows
against the generator's actual `LESSON_COMPETITORS`.

From the repository root:

```bash
python3 generators/f505996a2fdc/workspace/qualification.py \
  --seeds 32 --starts 12 \
  --out ../checks/f505996a2fdc_qualification.json
```

This is deliberately not independent label evidence: it uses the generator's
Python authority mirror. Use the Racket-backed `arcpuzzles lesson-census` report
for source-bound labels and hashes.
