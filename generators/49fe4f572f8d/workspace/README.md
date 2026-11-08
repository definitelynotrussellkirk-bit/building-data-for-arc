# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here. The selected implementation is `../generator.py`; workspace drafts are never automatically selected.

## Lesson identifiability census

`lesson_probe.py` is a source-bound, production-path audit for the complete five-demo teaching unit. Run it from the packet root through the verified Racket wrapper:

```bash
python3 run_with_racket.py python3 \
  generators/49fe4f572f8d/workspace/lesson_probe.py \
  --lessons-per-band 100 \
  --out ../checks/lesson-probe-final.json
```

The probe uses `puzzle_generators.runner.run_one`, the authoritative canonical Racket program, the profile-floor pinned seed recipe, sample-index stride 11, and every declared `LESSON_COMPETITORS` / `CANONICAL_SHORTCUTS` entry from the loaded generator. It records source hashes, materialization errors, complete-lesson outcomes, unique inputs, observed domain values, per-band counts, cyclic start residues, and concrete survivor examples. It exits nonzero when a declared rival survives any lesson, a canonical shortcut is invalid, the lesson hook disagrees, or generation fails.
