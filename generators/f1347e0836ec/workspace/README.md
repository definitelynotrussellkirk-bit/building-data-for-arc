# Workspace

The selected implementation is `../generator.py`. Workspace tools are not automatically selected as generators.

## Whole-lesson rival census

`lesson_probe.py` is a source-bound regression tool for the four-profile teaching schedule. It loads `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS` directly from the selected generator, verifies canonical shortcut fit, and checks every cyclic schedule start.

From the repository root:

```bash
PYTHONPATH=shared/runtime python3 \
  generators/f1347e0836ec/workspace/lesson_probe.py \
  --lessons-per-band 100 \
  --seed-start 0 \
  --require-no-survivors \
  --out ../checks/f1347e0836ec_lesson_probe_final.json
```

The report binds generator, canonical-ledger, probe, version, and rule hashes. It reports pair occurrences and unique inputs separately. Its claim is finite and limited to the live declared rival set; repository Racket stages independently check the Python mirror against the selected authority.
