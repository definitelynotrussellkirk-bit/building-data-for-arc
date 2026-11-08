# Workspace

`lesson_probe.py` is a reusable, source-bound lesson-level identifiability probe for this task. It reads the generator's actual `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, and `WITNESS_RIVALS`; verifies each shortcut against every usable canonical pair; then assembles non-overlapping 3-demo/1-query lessons from the actual default sampler.

Run from `repo/`:

```bash
python3 ../run_with_racket.py python3 generators/c782972f840b/workspace/lesson_probe.py \
  --lessons-per-band 100 --out ../checks/c782972f840b_lesson_probe.json
```

The selected implementation is `../generator.py`. Workspace tools are evidence and development aids; they are not selected generators.
